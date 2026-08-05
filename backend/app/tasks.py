import json
import logging
from pathlib import Path

from celery import shared_task
from django.conf import settings
from google import genai
from google.genai import errors

from .models import (
    Offer,
)
from .services.ai_extractor import (
    consolidate_extracted_data,
    get_flyer_images,
    process_flyers_batch,
    save_extracted_data,
)
from .services.scraper import download_supermarket_flyers, get_active_supermarkets

logger = logging.getLogger(__name__)


def _handle_extraction_error(task_instance, error: Exception, market_folder: str):
    """
    Handles exceptions during AI extraction and triggers Celery retries if needed.
    """
    if isinstance(error, json.JSONDecodeError):
        logger.error(f"JSON decode error for {market_folder}: {error}")
        raise task_instance.retry(exc=error, countdown=30) from error

    if isinstance(error, errors.ClientError):
        error_str = str(error)
        if "429" not in error_str:
            logger.error(f"Client error for {market_folder}: {error}")
            raise error

        is_per_minute = "perminute" in error_str.lower()
        retry_delay = 60 if is_per_minute else 86400

        if is_per_minute:
            logger.warning(
                f"Rate limit (per minute) exceeded for {market_folder}",
                "Re-queuing for {retry_delay}s.",
            )
        else:
            logger.critical(
                f"Daily quota exceeded for {market_folder}. Re-queuing for {retry_delay}s."
            )

        raise task_instance.retry(exc=error, countdown=retry_delay, max_retries=None) from error

    logger.error(f"Error in {market_folder}: {error}")
    raise error


@shared_task(bind=True, rate_limit="14/m", max_retries=3)
def extract_supermarket_flyers_data(self, market_folder: str, url: str = None):
    """
    Consumes flyer images from a supermarket folder, sending multiple images per request
    to Google Gemini AI. Consolidates the results and saves them to a JSON file.
    """

    target = Path(market_folder)
    images = get_flyer_images(target)

    if not images:
        logger.info(f"No flyer images found in path: {market_folder}")
        return {"status": "skipped", "reason": "No images found"}

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    batch_size = 15
    extracted_batches = []

    for batch_start in range(0, len(images), batch_size):
        batch_images = images[batch_start : batch_start + batch_size]

        try:
            logger.info(
                f"Processing batch {batch_start // batch_size + 1}"
                f" ({len(batch_images)} flyers) from {market_folder}"
            )

            validated_data = process_flyers_batch(client, batch_images)
            extracted_batches.append(validated_data)

        except Exception as e:
            _handle_extraction_error(self, e, market_folder)

    consolidated_data = consolidate_extracted_data(extracted_batches)

    # Saving JSON in the same folder as flyers
    output_filepath = target / "extracted_data.json"
    save_extracted_data(consolidated_data, output_filepath)

    return {"status": "success", "items_extracted": len(consolidated_data["items"])}


@shared_task
def scrap_supermarket_page(url: str):
    """
    Scrapes a specific supermarket page and downloads all available flyer images.
    This task runs in parallel for each supermarket link found on the landing index.
    """

    try:
        # If this supermarket link has already been scrapped, we skip
        if Offer.objects.filter(url=url).exists():
            logger.info(f"Skipping {url}: Already processed.")
            return

        # Call the scraper service
        folder_path, download_count = download_supermarket_flyers(url)

        if download_count > 0 and folder_path:
            logger.info(f"Downloaded {download_count} images for {url}")
            extract_supermarket_flyers_data.delay(str(folder_path), url)

    except Exception as e:
        logger.error(f"Error when scraping the Supermarket page ({url}): {e}")


@shared_task
def scrap_home_page():
    """
    This function scraps the home page of the "https://encartesdf.com.br/" URL.
    For each supermarket link found, it triggers a background download task.
    """

    try:
        urls = get_active_supermarkets()
        logger.info(f"Home Page analysis finished. Found {len(urls)} active links.")

        for market_url in urls:
            scrap_supermarket_page.delay(market_url)

    except Exception as e:
        logger.error(f"Error when scraping the Home Page: {e}")
