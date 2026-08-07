import json
import logging
import os
from pathlib import Path

from django.conf import settings
from django.db import connection, transaction
from google import genai
from google.genai import types
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..models import BranchProductOffer, Category, Offer, ParentSupermarket, Product
from ..utils import validate_extracted_flyer_json

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-3.1-flash-lite"
PROMPT_TEXT = """
Sua tarefa é analisar os panfletos de produtos de mercado fornecidos. Extrair todos os produtos,
preços e informações do panfleto e retorná-los em um formato JSON estrito e padronizado.

# Regras de Extração e Limpeza:

- Nome: Extraia o nome do produto juntamente com sua variedade essencial (Ex: "Maçã Verde",
"Banana Nanica", "Alface Crespa", "Patinho", "Leite Integral"). O campo "brand" deve conter o
nome do fabricante ou marca (ex: "Pringles"), e por isso é proibido repetir o valor de "brand"
dentro do campo "name". Se o produto for um Pack ou Fardo, adicione apenas essa condição ao nome
(Ex: "Cerveja Pack"). Mesmo que o produto seja amplamente conhecido pelo nome da marca (ex:
Pringles, Bombril, Coca-Cola), extraia o substantivo comum para o 'name' (Batata, Esponja de Aço,
Refrigerante) e o nome próprio para 'brand'.
É estritamente proibido incluir adjetivos mercadológicos, métodos de produção, características
de embalagem ou termos de qualidade (Ex: remova palavras como "Hidropônica", "Premium",
"Selecionada", "Fresca", "Limpa", "Tipo 1", "Tradicional").
O objetivo é um nome limpo para comparação de preços.
Exemplos de limpeza:
"Alface Crespa Hidropônica" -> "Alface Crespa"
"Maçã Verde Selecionada Premium" -> "Maçã Verde"
"Feijão Carioca Tipo 1" -> "Feijão Carioca"

- Marca: Se houver marca explícita (ex: "Tio João", "Coca-Cola", "Nestlé"), separe-a do nome e
especifique-a na coluna "brand". Se uma palavra for classificada como "brand", ela está
estritamente proibida de aparecer no campo 'name'.

- Medida e Unidade: Se o texto diz "5kg", separe em colunas de medida e de unidade
(ex: medida=5, unidade='kg'). Para a coluna de unidades, você pode considerar um dos seguintes
valores: "g", "kg", "un", "l" ou "ml". Se o produto for vendido por peso (ex:"Bife de Chorizo Kg"),
use medida=1.0 e a unidade de medida normalmente, identificadas pelas colunas "unit_of_measure"
e "measure".

- Preço: Converta para formato decimal (ponto para decimais). Ex: "R$ 7,99" vira 7.99. Se houver
mais de um preço para o mesmo produto (ex: "Varejo" e "Clube", "Atacado"), crie vários itens
separados no JSON para o mesmo produto, diferenciando-os pelo seu tipo: "Varejo", "Clube",
"Atacado", "Cartão", etc. Se não tiver o tipo especificado no produto, considere "Varejo"
como o padrão. O preço está especificado na coluna "price".

- Data de Validade: Procure no rodapé ou cabeçalho a data de validade da oferta
(ex: "Válido até 15/10"). Retorne no formato YYYY-MM-DD. Está especificada na coluna
"expiration_date".

- Mercado: Identifique o nome do mercado pelo logotipo ou texto de destaque. Está especificado
pela coluna "supermarket".

- Categoria: O produto DEVE ser classificado em uma destas exatas categorias:
Carnes, Grãos, Óleo, Café/Açúcar, Laticínios, Hortifruti, Ovos, Limpeza, Higiene, Massas,
Molhos, Doces, Enlatados, Bebidas. Retorne o valor na coluna "category".

Formato de Saída (JSON): Retorne APENAS um objeto JSON válido com a seguinte estrutura, sem markdown
em volta, com todos os itens do mercado:

{
  "supermarket": "Nome do Mercado",
  "expiration_date": "YYYY-MM-DD",
  "items": [
    {
      "name": "String (Ex: Arroz Branco)",
      "category": "String (Ex: Grãos)",
      "type": "String (Ex: Varejo)",
      "brand": "String (Ex: Camil, ou \"\" se não tiver)",
      "measurement_unit": "String (kg, g, l, ml, un)",
      "measurement": Float (Ex: 5.0),
      "price": Float (Ex: 21.90)
    }
  ]
}
"""


def get_flyer_images(folder: Path) -> list[Path]:
    """
    Retrieves all valid flyer images from inside a folder.
    """
    if not folder.exists():
        logger.error(f"Folder path not found: {folder}")
        return []

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = [f for f in folder.iterdir() if f.suffix.lower() in valid_extensions]

    return sorted(images)


def _build_ai_payload(images: list[Path]) -> list[types.Part]:
    """
    Builds the payload with the images and prompt that'll be used to
    communicate with the Gemini API.
    """
    mime_types_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    payload = []
    for image in images:
        image_bytes = image.read_bytes()
        mime_type = mime_types_map.get(image.suffix.lower(), "image/jpeg")
        payload.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    payload.append(PROMPT_TEXT)
    return payload


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _generate_content_with_retry(contents: list[types.Part]) -> str:
    """
    Wraps the API call with exponential backoff to manage short burst
    rate limits (requests per minute).
    """

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    return response.text


def process_flyers_batch(images: list[Path]) -> dict:
    """
    Processes a single batch of flyer images using Gemini AI.
    Builds the payload, calls the API, parses the JSON, and validates it.
    """

    contents = _build_ai_payload(images)
    response_text = _generate_content_with_retry(contents)

    data = json.loads(response_text)
    validated_data = validate_extracted_flyer_json(data)

    return validated_data


def consolidate_extracted_data(batches: list[dict]) -> dict:
    """
    Consolidates multiple batches of extracted flyer data into a single dictionary.
    Extracts a single global supermarket name and expiration date from the batches.
    """
    global_supermarket = None
    global_expiration = None
    all_items = []

    for batch_data in batches:
        global_supermarket = global_supermarket or batch_data.get("supermarket")
        global_expiration = global_expiration or batch_data.get("expiration_date")
        all_items.extend(batch_data.get("items", []))

    return {
        "supermarket": global_supermarket,
        "expiration_date": global_expiration,
        "items": all_items,
    }


def save_extracted_data(data: dict, output_filepath: Path):
    """
    Saves the consolidated JSON data to the specified file path
    and configures permissions.
    """
    with open(output_filepath, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)

    os.chmod(output_filepath, 0o666)


def save_extracted_data_to_db(data: dict, url: str):
    """
    Saves the consolidated JSON data into the database using atomic transactions.
    It maps the extracted supermarket to a ParentSupermarket and links all
    its existing branches to the new Offer.
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(8472935)")

            offer, _ = Offer.objects.update_or_create(
                url=url, defaults={"expiration_date": data["expiration_date"]}
            )

            parent_supermarket, _ = ParentSupermarket.objects.get_or_create(
                name=data["supermarket"]
            )
            branches = list(parent_supermarket.branches.all())

            for item in data["items"]:
                try:
                    category = Category.objects.get(name__iexact=item["category"])
                except Category.DoesNotExist:
                    logger.warning(
                        f"Category '{item['category']}' not found for product '{item['name']}'.",
                        "Skipping.",
                    )
                    continue

                product, _ = Product.objects.get_or_create(
                    name=item["name"],
                    brand=item["brand"],
                    measurement=item["measurement"],
                    measurement_unit=item["measurement_unit"].upper(),
                    category=category,
                )

                for branch in branches:
                    BranchProductOffer.objects.update_or_create(
                        product=product,
                        branch_supermarket=branch,
                        offer=offer,
                        defaults={"price": item["price"]},
                    )

    except Exception as e:
        logger.error(f"Failed to save data to database for {url}: {e}")
        raise
