import logging
import os
import tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

FLYERS_BASE_DIR = Path(tempfile.gettempdir()) / "flyers"
FLYERS_URL = "https://encartesdf.com.br/"


def _scrap(url: str) -> BeautifulSoup:
    """
    Scraps a webpage and returns its contents as a BeautifulSoup object.
    If the request's status_code != 200, it'll throw an error.
    """

    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    return BeautifulSoup(response.text, "html.parser")


def _get_supermarkets_links(soup: BeautifulSoup) -> list[str]:
    """
    Reads a BeautifulSoup object and returns any links
    that lead to a supermarket's page.
    """

    h1_tags = soup.select(".main-title")
    links_found = []

    for h1_tag in h1_tags:
        a_tag = h1_tag.select_one("a")

        # If there's no supermarket link, we skip
        if not a_tag:
            continue

        # If the supermarket offer is expired, we skip
        if a_tag.select_one(".badge-vencido"):
            continue

        market_url = a_tag.get("href")
        links_found.append(market_url)

    return links_found


def _get_flyers_images_links(soup: BeautifulSoup) -> list[str]:
    """
    Reads a BeautifulSoup object and returns any links related
    to a flyer image.
    """

    # Represent the flyers list in the page
    text_container = soup.select_one(".text")
    if not text_container:
        return []

    img_tags = text_container.find_all("img", class_=lambda c: c and c.startswith("wp-image"))

    flyers_links = []

    for img_tag in img_tags:
        src = img_tag.get("data-src") or img_tag.get("src")
        if src:
            flyers_links.append(src)

    return flyers_links


def _create_supermarket_folder(supermarket_url: str) -> Path:
    """
    Creates the supermarket's folder where the flyers will be saved from
    the slug taken from a link, and returns its address as a Path object.
    """

    slug = supermarket_url.strip("/").split("/")[-1]
    FLYERS_BASE_DIR.mkdir(parents=True, exist_ok=True)

    folder_path = Path(tempfile.mkdtemp(prefix=f"{slug}_", dir=FLYERS_BASE_DIR))
    os.chmod(folder_path, 0o777)

    return folder_path


def get_active_supermarkets() -> list[str]:
    """
    Fetches the home page and returns a list of active supermarket URLs.
    """
    soup = _scrap(FLYERS_URL)
    return _get_supermarkets_links(soup)


def _download_images_to_folder(images_links: list[str], target_folder: Path) -> int:
    """
    Downloads a list of image URLs and saves them to the given folder.
    Returns the total count of successfully downloaded images.
    """

    download_count = 0

    for index, link in enumerate(images_links):
        # Checks if it was possible to download the image
        response = requests.get(link, stream=True)
        if response.status_code != 200:
            logger.warning(f"Failed to download image {link} (Status: {response.status_code})")
            continue

        file_path = target_folder / f"{index:02d}.jpg"

        # Saves the downloaded image
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        download_count += 1

    return download_count


def download_supermarket_flyers(supermarket_url: str) -> tuple[Path, int]:
    """
    Scraps a single supermarket link, downloads its flyers images,
    and returns a tuple containing the folder path where they were saved
    and the total count of downloaded images.
    """

    soup = _scrap(supermarket_url)
    images_links = _get_flyers_images_links(soup)

    if not images_links:
        return None, 0

    supermarket_folder = _create_supermarket_folder(supermarket_url)
    download_count = _download_images_to_folder(images_links, supermarket_folder)

    return supermarket_folder, download_count
