import json
import logging
import os
import tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from celery import chord, shared_task
from django.conf import settings
from google import genai
from google.genai import types
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .models import Offer
from .utils import validate_extracted_flyer_json

logger = logging.getLogger(__name__)

FLYERS_BASE_DIR = Path(tempfile.gettempdir()) / "flyers"
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

- Canto superior esquerdo e canto inferior direito: Para cada produto, especifique as
coordenadas em pixels (x, y) do panfleto onde está localizado a imagem do produto, para recorte
e armazenamento posterior da imagem no banco de dados. Estão especificados pela coluna "top_left"
e "bottom_right".

Formato de Saída (JSON): Retorne APENAS um objeto JSON válido com a seguinte estrutura, sem markdown
em volta, com todos os itens do mercado:

{
  "supermarket": "Nome do Mercado",
  "expiration_date": "YYYY-MM-DD",
  "items": [
    {
      "name": "String (Ex: Arroz Branco)",
      "type": "String (Ex: Varejo)",
      "brand": "String ou null (Ex: Camil)",
      "unit_of_measure": "String (kg, g, l, ml, un)",
      "measure": Float (Ex: 5.0),
      "price": Float (Ex: 21.90),
      "top_left": [x, y],
      "bottom_right": [x, y],
    }
  ]
}
"""


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def generate_content_with_retry(client, model_name, contents):
    """
    Wraps the API call with exponential backoff to manage short burst
    rate limits (requests per minute).
    """
    return client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )


@shared_task(bind=True, rate_limit="14/m", max_retries=3)
def extract_supermarket_flyers_data(self, market_folder: str):
    """
    Consumes flyer images from a supermarket folder, sending multiple images per request
    to Google Gemini AI. Consolidates the results and saves them to a JSON file.
    """

    target = Path(market_folder)
    if not target.exists():
        logger.error(f"Supermarket flyer path not found: {market_folder}")
        return {"status": "error", "reason": "Path not found"}

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = sorted([f for f in target.iterdir() if f.suffix.lower() in valid_extensions])

    if not images:
        logger.info(f"No flyer images found in path: {market_folder}")
        return {"status": "skipped", "reason": "No images found"}

    mime_types_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    batch_size = 15
    extracted_batches = []

    for batch_start in range(0, len(images), batch_size):
        batch_images = images[batch_start : batch_start + batch_size]
        contents = []

        for img_path in batch_images:
            image_bytes = img_path.read_bytes()
            mime_type = mime_types_map.get(img_path.suffix.lower(), "image/jpeg")
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        contents.append(PROMPT_TEXT)

        try:
            logger.info(
                f"Processing batch {batch_start // batch_size + 1}"
                f" ({len(batch_images)} flyers) from {market_folder} using {GEMINI_MODEL}"
            )

            response = generate_content_with_retry(client, GEMINI_MODEL, contents)

            data = json.loads(response.text)
            validated_data = validate_extracted_flyer_json(data)

            extracted_batches.append(validated_data)

        except Exception as exception:
            exception_string = str(exception)
            if "429" in exception_string:
                if "PerMinute" in exception_string:
                    retry_delay_seconds = 60
                    logger.warning(
                        f"""Error 429 (PerMinute rate limit exceeded) for {market_folder}.
                        Re-queuing task for 60 seconds."""
                    )
                else:
                    retry_delay_seconds = 86400
                    logger.critical(
                        f"""Error 429 (PerDay daily quota exceeded) for {market_folder}.
                        Re-queuing task for 24 hours."""
                    )

                raise self.retry(
                    exc=exception,
                    countdown=retry_delay_seconds,
                    max_retries=None,
                ) from exception

            else:
                logger.error(f"Error in {market_folder} with {GEMINI_MODEL}: {exception}")
                raise

    global_supermarket = None
    global_expiration = None
    all_items = []

    # Running through all files trying to find out the supermarket's name and
    # the expiration date, since it could be in any image
    for batch_data in extracted_batches:
        if batch_data.get("supermarket") and not global_supermarket:
            global_supermarket = batch_data["supermarket"]

        if batch_data.get("expiration_date") and not global_expiration:
            global_expiration = batch_data["expiration_date"]

        all_items.extend(batch_data.get("items", []))

    consolidated_json = {
        "supermarket": global_supermarket,
        "expiration_date": global_expiration,
        "items": all_items,
    }

    # Saving JSON in the same folder as flyers
    output_filepath = target / "extracted_data.json"
    with open(output_filepath, "w", encoding="utf-8") as json_file:
        json.dump(consolidated_json, json_file, indent=2, ensure_ascii=False)

    os.chmod(output_filepath, 0o666)
    logger.info(f"Extraction finished for {market_folder}. {len(all_items)} items saved.")


@shared_task
def scrap_supermarket_page(url: str):
    """
    Scrapes a specific supermarket page and downloads all available flyer images.
    This task runs in parallel for each supermarket link found on the landing index.
    It collects and returns execution statistics to feed the final orchestration report.
    """

    FLYERS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    market_slug = url.strip("/").split("/")[-1]

    # metrics dictionary to be used in the final summary report
    metrics = {"market": market_slug, "status": "success", "downloaded_images": 0, "reason": ""}

    try:
        # If this supermarket link has already been scrapped, we skip
        if Offer.objects.filter(url=url).exists():
            metrics["status"] = "skipped"
            metrics["reason"] = "Already processed"
            return metrics

        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Creating a temporary folder to download the supermarket's flyers
        new_temp_folder = Path(
            tempfile.mkdtemp(
                prefix=f"{market_slug}_",
                dir=FLYERS_BASE_DIR,
            )
        )

        os.chmod(new_temp_folder, 0o777)

        # Represent the flyers list in the page
        img_tags = soup.select_one(".text").find_all(
            "img", class_=lambda c: c and c.startswith("wp-image")
        )
        download_count = 0

        for index, img_tag in enumerate(img_tags):
            src = img_tag.get("data-src") or img_tag.get("src")
            if not src:
                continue

            # Trying to download the flyer image
            response = requests.get(src, stream=True)
            if response.status_code != 200:
                logger.warning(f"Failed to download image {src} (Status: {response.status_code})")
                continue

            file_name = f"{index:02d}.jpg"
            file_path = new_temp_folder / file_name

            # Saving the image in a temp file
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            download_count += 1

        # Updating metrics for the final summary report
        metrics["downloaded_images"] = download_count
        extract_supermarket_flyers_data.delay(str(new_temp_folder))

        return metrics

    except Exception as e:
        logger.error(f"Error when scraping the Supermarket page ({url}): {e}")

        # Capturing the failure details to include in the final report
        metrics["status"] = "error"
        metrics["reason"] = str(e)
        return metrics


@shared_task
def generate_scraping_report(results):
    """
    Triggered automatically by Celery if and only when
    every single queued supermarket task completes execution.
    """

    if not results:
        logger.warning("No scraping results collected for the report.")
        return

    total_markets = len(results)
    total_images = sum(item["downloaded_images"] for item in results if item)
    successful_markets = sum(1 for item in results if item and item["status"] == "success")
    skipped_markets = sum(1 for item in results if item and item["status"] == "skipped")
    failed_markets = sum(1 for item in results if item and item["status"] == "error")

    report = f"""
======================================================================
📊 FINAL SCRAPING REPORT - Compare prices
======================================================================
🏁 Execution Status: COMPLETED
🏪 Total Establishments Evaluated: {total_markets}
✅ Supermarkets Processed Successfully: {successful_markets}
⏩ Supermarkets Skipped (Existing Data): {skipped_markets}
❌ Supermarkets with Execution Errors: {failed_markets}
🖼️ Total Images/Flyers Downloaded: {total_images}

----------------------------------------------------------------------
📋 Detailed Breakdown per Establishment:
----------------------------------------------------------------------
"""
    for item in results:
        if not item:
            continue
        icons = {
            "success": "✅",
            "skipped": "⏩",
            "error": "❌",
        }
        status_icon = icons.get(item["status"], icons["error"])
        reason_str = f" ({item['reason']})" if item["reason"] else ""
        report += (
            f"  {status_icon} {item['market'].upper()}:"
            f" {item['downloaded_images']} image(s) saved{reason_str}\n"
        )

    report += "======================================================================"

    print(report)
    logger.info("Scraping workflow completed execution.")


@shared_task
def scrap_home_page():
    """
    This function scraps the home page of the "https://encartesdf.com.br/" URL.
    For each supermarket link found, it compiles a chord execution graph
    to trigger a unified summary report once all downloads finish.
    """

    URL = "https://encartesdf.com.br/"
    FLYERS_BASE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Each supermarket link ('a' tag) is located in the following 'h1' tags.
        h1_tags = soup.select(".main-title")

        # Array created to accumulate task signatures for the chord pipeline
        tasks_to_run = []

        for h1_tag in h1_tags:
            a_tag = h1_tag.select_one("a")

            # If there's no supermarket link, we skip
            if not a_tag:
                continue

            # If the supermarket offer is expired, we skip
            if a_tag.select_one(".badge-vencido"):
                continue

            market_url = a_tag.get("href")

            # Appending active scraping tasks to the batch signature array
            tasks_to_run.append(scrap_supermarket_page.s(market_url))

        # Launching the parallel execution group and binding it to the report callback
        if tasks_to_run:
            logger.info(
                f"""Home Page analysis finished.
                Launching chord workflow for {len(tasks_to_run)} tasks."""
            )
            chord(tasks_to_run)(generate_scraping_report.s())
        else:
            logger.info("No active supermarket offers found to process.")

    except Exception as e:
        logger.error(f"Error when scraping the Home Page: {e}")
