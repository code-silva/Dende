import json
import re
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


def sanitize_json_response(text: str) -> str:
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    start = text.find("{")
    if start == -1:
        return text.strip()
    text = text[start:]
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text)
    return json.dumps(obj)


def remove_accents(text: str) -> str:
    """
    Returns the string without any accents.
    """

    if not text:
        return ""

    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
