import unicodedata
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FlyerItemSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    type: str | None = "Varejo"
    brand: str | None = None
    unit_of_measure: str | None = None
    measure: float | None = None
    price: float
    top_left: list[int] | None = None
    bottom_right: list[int] | None = None


class FlyerExtractionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    supermarket: str | None = None
    expiration_date: date | None = None
    items: list[FlyerItemSchema] = Field(default_factory=list)


def validate_extracted_flyer_json(data: Any) -> dict:
    """
    Validates and normalizes the extracted flyer JSON using Pydantic schemas.
    Raises ValueError or ValidationError if the structure is invalid.
    """

    if not isinstance(data, dict):
        raise ValueError("The JSON return should be a dict.")

    validated = FlyerExtractionSchema.model_validate(data)
    return validated.model_dump(mode="json")


def remove_accents(text: str) -> str:
    """
    Returns the string without any accents.
    """

    if not text:
        return ""

    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize_search_query(text: str | None) -> str:
    """
    Normalizes a search term for accent-insensitive fuzzy matching:
    trims whitespace, lowercases and strips accents/diacritics.
    """

    if not text:
        return ""

    return remove_accents(text.strip().lower())
