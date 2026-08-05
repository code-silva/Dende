import unicodedata
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FlyerItemSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    category: str
    brand: str
    measurement_unit: Literal["KG", "G", "L", "ML", "UN", "kg", "g", "l", "ml", "un"]
    measurement: float
    price: float


class FlyerExtractionSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    supermarket: str
    expiration_date: date
    items: list[FlyerItemSchema] = Field(min_length=1)


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
