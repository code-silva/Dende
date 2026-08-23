import json
import logging
import shutil
from difflib import SequenceMatcher
from pathlib import Path

from celery import shared_task
from google.genai import errors
from pydantic import ValidationError

from .models import (
    Offer,
    ParentSupermarket,
)
from .services.ai_extractor import (
    consolidate_extracted_data,
    extract_branches_locations,
    get_flyer_images,
    process_flyers_batch,
    save_extracted_data,
    save_extracted_data_to_db,
)
from .services.geocoding import geocode_address
from .services.scraper import download_supermarket_flyers, get_active_supermarkets

logger = logging.getLogger(__name__)

ADDRESS_SIMILARITY_THRESHOLD = 0.7


def _handle_extraction_error(task_instance, error: Exception, market_folder: str):
    """
    Handles exceptions during AI extraction and triggers Celery retries if needed.
    """
    if isinstance(error, ValidationError):
        logger.error(f"Pydantic validation error for {market_folder}: {error}")
        raise ValueError("Aborting task: Pydantic validation failed (e.g., missing date).")

    if isinstance(error, json.JSONDecodeError):
        logger.error(f"JSON decode error for {market_folder}: {error}")
        raise task_instance.retry(countdown=30)

    if isinstance(error, errors.ClientError):
        error_str = str(error)
        if "429" not in error_str:
            logger.error(f"Client error for {market_folder}: {error}")
            raise error

        import random

        is_daily = "perday" in error_str.lower() or "daily" in error_str.lower()
        retry_delay = 86400 if is_daily else 60 + random.randint(10, 60)

        if is_daily:
            logger.critical(
                f"Daily quota exceeded for {market_folder}. Re-queuing for {retry_delay}s."
            )
        else:
            logger.warning(
                f"Rate limit exceeded for {market_folder}. Re-queuing for {retry_delay}s."
            )

        raise task_instance.retry(countdown=retry_delay, max_retries=9999)

    logger.error(f"Error in {market_folder}: {error}")
    raise error


def _extract_and_geocode_branches(consolidated_data: dict, text_path: Path):
    """
    Extracts unstructured branch addresses from the page text,
    geocodes them, deduplicates against existing branches,
    and appends to consolidated_data.
    """
    if not text_path.exists():
        return

    page_text = text_path.read_text(encoding="utf-8")

    try:
        extracted_branches = extract_branches_locations(page_text)
        geocoded_branches = []

        parent_name = consolidated_data.get("supermarket")
        existing_addresses = []
        if parent_name:
            parent = ParentSupermarket.objects.filter(name=parent_name).first()
            if parent:
                existing_addresses = []
                for b in parent.branches.all():
                    parts = filter(bool, [b.city, b.neighborhood, b.street, b.number])
                    existing_addresses.append(" ".join(parts).lower())

        for branch in extracted_branches:
            address = branch.get("address")
            if not address:
                continue

            address_lower = address.lower()
            is_new = True

            for existing_addr in existing_addresses:
                if not existing_addr:
                    continue
                if existing_addr in address_lower or address_lower in existing_addr:
                    is_new = False
                    break
                similarity = SequenceMatcher(None, existing_addr, address_lower).ratio()
                if similarity > ADDRESS_SIMILARITY_THRESHOLD:
                    is_new = False
                    break

            if is_new:
                search_address = f"{parent_name}, {address}" if parent_name else address
                geocoded = geocode_address(search_address)
                if geocoded:
                    branch.update(geocoded)
                    geocoded_branches.append(branch)

        consolidated_data["branches"] = geocoded_branches
    except Exception as e:
        logger.error(f"Error extracting and geocoding branches: {e}")


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

    batch_size = 15
    extracted_batches = []

    for batch_start in range(0, len(images), batch_size):
        batch_images = images[batch_start : batch_start + batch_size]

        logger.info(
            f"Processing batch {batch_start // batch_size + 1}"
            f" ({len(batch_images)} flyers) from {market_folder}"
        )

        try:
            validated_data = process_flyers_batch(batch_images)
            extracted_batches.append(validated_data)
        except Exception as e:
            _handle_extraction_error(self, e, market_folder)

    consolidated_data = consolidate_extracted_data(extracted_batches)

    text_path = target / "page_text.txt"
    _extract_and_geocode_branches(consolidated_data, text_path)

    # Saving JSON in the same folder as flyers
    output_filepath = target / "extracted_data.json"
    save_extracted_data(consolidated_data, output_filepath)

    # Save to Database
    logger.info(f"Saving extracted data from {market_folder} to database.")
    save_extracted_data_to_db(consolidated_data, url)

    shutil.rmtree(target, ignore_errors=True)

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
        logger.info(
            f"Home Page analysis finished. Found {len(urls)} active links (limited for testing)."
        )

        for market_url in urls:
            scrap_supermarket_page.delay(market_url)

    except Exception as e:
        logger.error(f"Error when scraping the Home Page: {e}")
