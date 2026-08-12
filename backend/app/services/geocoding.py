import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def geocode_address(address: str) -> dict:
    """
    Sends an address string to the Google Maps Geocoding API and returns
    its coordinates and structured address components.
    """

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": settings.GOOGLE_MAPS_API_KEY,
        "language": "pt-BR",
        "region": "br",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            logger.warning(
                f"Geocoding API returned status: {data.get('status')} for address: {address}"
            )
            return

        results = data["results"][0]
        location = results["geometry"]["location"]

        city = ""
        state = ""

        for component in results.get("address_components"):
            if "administrative_area_level_2" in component.get("types"):
                city = component.get("long_name")
            if "administrative_area_level_1" in component.get("types"):
                state_short = component.get("short_name")
                if len(state_short) == 2:
                    state = state_short.upper()

        return {
            "lat": location["lat"],
            "lng": location["lng"],
            "city": city,
            "state": state,
            "formatted_address": results.get("formatted_address"),
        }

    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
        return None
