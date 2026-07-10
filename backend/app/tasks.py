import json
import logging
import tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from celery import chord, shared_task
from ..core import settings
from google import genai
from google.genai import types

from .models import Offer
from .utils import validate_extracted_flyer_json

logger = logging.getLogger(__name__)

FLYERS_BASE_DIR = Path(tempfile.gettempdir()) / "flyers"

PROMPT_TEXT = """
Sua tarefa é analisar os panfletos de produtos de mercado fornecidos. Extrair todos os produtos, preços e informações do panfleto e retorná-los em um formato JSON estrito e padronizado.

# Regras de Extração e Limpeza:

- Nome: Extraia apenas a categoria genérica do produto para a coluna "name" (ex: "Batata"). O campo "brand" deve conter o nome do fabricante ou marca (ex: "Pringles"). É proibido repetir o valor de "brand" dentro do campo "name". Se o produto for um Pack ou Fardo, adicione apenas essa condição ao nome (Ex: "Cerveja Pack"). Mesmo que o produto seja amplamente conhecido pelo nome da marca (ex: Pringles, Bombril, Coca-Cola), extraia o substantivo comum para o 'name' (Batata, Esponja de Aço, Refrigerante) e o nome próprio para 'brand'.
- Marca: Se houver marca explícita (ex: "Tio João", "Coca-Cola", "Nestlé"), separe-a do nome e especifique-a na coluna "Brand". Se uma palavra for classificada como 'brand', ela está estritamente proibida de aparecer no campo 'name'.
- Medida e Unidade: Se o texto diz "5kg", separe em colunas de medida e de unidade (ex: medida=5, unidade='kg'). Para a coluna de unidades, você pode considerar um dos seguintes valores: "g", "kg", "un", "l" ou "ml". Se o produto for vendido por peso (ex: "Bife de Chorizo Kg"), use medida=1.0 e a unidade de medida normalmente, identificadas pelas colunas "unit_of_measure" e "measure".
- Preço: Converta para formato decimal (ponto para decimais). Ex: "R$ 7,99" vira 7.99. Se houver mais de um preço para o mesmo produto (ex: "Varejo" e "Clube", "Atacado"), crie vários itens separados no JSON para o mesmo produto, diferenciando-os pelo seu tipo: "Varejo", "Clube", "Atacado", "Cartão", etc. Se não tiver o tipo especificado no produto, considere "Varejo" como o padrão. O preço está especificado na coluna "price".
- Data de Validade: Procure no rodapé ou cabeçalho a data de validade da oferta (ex: "Válido até 15/10"). Retorne no formato YYYY-MM-DD. Está especificada na coluna "expiration_date'.
- Mercado: Identifique o nome do mercado pelo logotipo ou texto de destaque. Está especificado pela coluna "supermarket".
- Canto superior esquerdo e canto inferior direito: Para cada produto, especifique as coordenadas em pixels (x, y) do panfleto onde está localizado a imagem do produto, para recorte e armazenamento posterior da imagem no banco de dados. Estão especificados pela coluna "top_left" e "bottom_right".

Formato de Saída (JSON): Retorne APENAS um objeto JSON com a seguinte estrutura, sem markdown em volta, com todos os itens do mercado:

JSON
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


@shared_task(bind=True)
def extract_supermarket_flyers_data(self, market_folder: str, url: str = None):
    """
    Consumes flyer images from a supermarket folder, sending up to 5 images per request
    along with the prompt to Google Gemini AI Studio requesting strict JSON.
    If a 429 quota exceeded error occurs, it alternates to the next free model.
    If all free models are exhausted, it keeps the task in the Celery queue.
    """

    target = Path(market_folder)
    if not target.exists():
        logger.error(f"Supermarket flyer path not found: {market_folder}")
        return {"status": "error", "reason": "Path not found"}

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    images = sorted([file for file in target.iterdir()])

    if not images:
        logger.info(f"No flyer images found in path: {market_folder}")
        return {"status": "skipped", "reason": "No images found"}

    mime_types_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    batch_size = 5
    extracted_batches = []

    for batch_start in range(0, len(images), batch_size):
        batch_images = images[batch_start:batch_start + batch_size]
        contents = []

        for img_path in batch_images:
            image_bytes = img_path.read_bytes()
            mime_type = mime_types_map.get(img_path.suffix.lower(), "image/jpeg")
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        contents.append(PROMPT_TEXT)

        last_error = None
        batch_extracted = False

        for model_name in settings.FREE_GEMINI_MODELS:
            try:
                logger.info(
                    f"Processing batch of {len(batch_images)} flyers from {market_folder} "
                    f"using model {model_name}"
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )

                data = json.loads(response.text)
                validated_data = validate_extracted_flyer_json(data)

                extracted_batches.append({
                    "model_used": model_name,
                    "images": [str(p) for p in batch_images],
                    "data": validated_data,
                })

                batch_extracted = True
                break

            except Exception as exc:
                code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                is_429 = code == 429 or "429" in str(exc)
                if is_429:
                    logger.warning(
                        f"Erro 429: Esgotamento de cota da API com o modelo {model_name}. "
                        "Alternando para o próximo modelo gratuito..."
                    )
                    last_error = exc
                    continue
                else:
                    logger.error(
                        f"Error processing flyers batch in {market_folder} with {model_name}: {exc}"
                    )
                    raise exc

        if not batch_extracted and last_error is not None:
            retry_delay = settings.GEMINI_QUOTA_RETRY_DELAY
            logger.warning(
                f"Esgotamento da cota em todos os modelos gratuitos "
                f"para a pasta {market_folder}. Colocando a tarefa na fila do Celery."
            )
        
            raise self.retry(exc=last_error, countdown=retry_delay)

    return {
        "status": "success",
        "market_folder": str(market_folder),
        "url": url,
        "extracted_batches": extracted_batches,
    }


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
        extract_supermarket_flyers_data.delay(str(new_temp_folder), url=url)

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
