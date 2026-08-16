import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _extract_basic_components(components: list) -> tuple[dict, dict, dict, str]:
    admin_areas = {}
    sublocalities = {}
    address_data = {
        "city": "",
        "state": "",
        "zip_code": None,
        "street": None,
        "number": None,
        "neighborhood": None,
    }
    neighborhood_default = None

    for component in components:
        types = component.get("types", [])
        long_name = component.get("long_name")

        for t in types:
            if t.startswith("administrative_area_level_"):
                try:
                    level = int(t.split("_")[-1])
                    admin_areas[level] = long_name
                except ValueError:
                    pass
            elif t.startswith("sublocality_level_"):
                try:
                    level = int(t.split("_")[-1])
                    sublocalities[level] = long_name
                except ValueError:
                    pass
            elif t == "sublocality":
                sublocalities[0] = long_name
            elif t == "neighborhood":
                neighborhood_default = long_name
            elif t == "postal_code":
                address_data["zip_code"] = long_name
            elif t == "route":
                if long_name.lower().startswith("setor "):
                    neighborhood_default = long_name
                else:
                    address_data["street"] = long_name
            elif t == "street_number":
                address_data["number"] = long_name

            if t == "administrative_area_level_1":
                state_short = component.get("short_name", "")
                if len(state_short) == 2:
                    address_data["state"] = state_short.upper()

    return address_data, admin_areas, sublocalities, neighborhood_default


def _resolve_neighborhood(sublocalities: dict, neighborhood_default: str) -> str:
    """
    Resolves the most specific neighborhood from Google Maps sublocalities.
    Scans from sublocality_level_5 down to level 1, then sublocality, then neighborhood.
    """

    for level in range(5, -1, -1):
        if level in sublocalities:
            return sublocalities[level]
    return neighborhood_default


def _apply_df_ultimate_fallback(components: list, current_city: str) -> str:
    """
    Fallback mechanism exclusively for the Federal District (DF).
    Searches all geographical text returned by Google Maps to find a match
    against a known list of 37 Administrative Regions (RAs).
    """

    current_city_lower = current_city.lower().strip()
    DF_RAS_MAP = {
        "26 de setembro": "26 de Setembro",
        "arapoanga": "Arapoanga",
        "arniqueira": "Arniqueira",
        "brazlândia": "Brazlândia",
        "candangolândia": "Candangolândia",
        "ceilândia": "Ceilândia",
        "cruzeiro": "Cruzeiro",
        "estrutural": "Estrutural",
        "fercal": "Fercal",
        "gama": "Gama",
        "guará": "Guará",
        "itapoã": "Itapoã",
        "jardim botânico": "Jardim Botânico",
        "lago norte": "Lago Norte",
        "lago sul": "Lago Sul",
        "núcleo bandeirante": "Núcleo Bandeirante",
        "octogonal": "Octogonal",
        "paranoá": "Paranoá",
        "park way": "Park Way",
        "planaltina": "Planaltina",
        "plano piloto": "Plano Piloto",
        "ponte alta": "Ponte Alta",
        "pôr do sol": "Pôr do Sol",
        "recanto das emas": "Recanto das Emas",
        "riacho fundo": "Riacho Fundo",
        "riacho fundo ii": "Riacho Fundo II",
        "scia": "SCIA",
        "sia": "SIA",
        "samambaia": "Samambaia",
        "santa maria": "Santa Maria",
        "sobradinho": "Sobradinho",
        "sobradinho ii": "Sobradinho II",
        "sol nascente": "Sol Nascente",
        "sol nascente/pôr do sol": "Sol Nascente/Pôr do Sol",
        "sudoeste": "Sudoeste",
        "sudoeste/octogonal": "Sudoeste/Octogonal",
        "são sebastião": "São Sebastião",
        "taguatinga": "Taguatinga",
        "varjão": "Varjão",
        "vicente pires": "Vicente Pires",
        "água quente": "Água Quente",
        "águas claras": "Águas Claras",
    }

    if current_city_lower in DF_RAS_MAP:
        return DF_RAS_MAP[current_city_lower]

    for component in components:
        types = set(component.get("types", []))
        if not types.intersection(
            {"route", "street_number", "postal_code", "country", "subpremise"}
        ):
            long_name = component.get("long_name", "").lower().strip()
            if long_name in DF_RAS_MAP:
                return DF_RAS_MAP[long_name]

            short_name = component.get("short_name", "").lower().strip()
            if short_name in DF_RAS_MAP:
                return DF_RAS_MAP[short_name]

    return current_city


def _resolve_city(address_data: dict, admin_areas: dict, components: list) -> str:
    """
    Resolves the city from the administrative areas.
    If the state is DF, it applies a top-down search (level 7 to 2) and the DF RA fallback.
    Otherwise, it returns the standard administrative_area_level_2.
    """

    city = ""
    if address_data["state"] == "DF":
        for level in range(7, 1, -1):
            if level in admin_areas:
                city = admin_areas[level]
                break

        return _apply_df_ultimate_fallback(components, city)

    return admin_areas.get(2, "")


def _parse_address_components(results: dict) -> dict:
    """
    Parses the address components from the Google Maps Geocoding API response
    and extracts structured data like city, state, street, etc.
    """

    components = results.get("address_components", [])
    address_data, admin_areas, sublocalities, n_default = _extract_basic_components(components)

    address_data["city"] = _resolve_city(address_data, admin_areas, components)
    address_data["neighborhood"] = _resolve_neighborhood(sublocalities, n_default)

    if address_data["neighborhood"] and address_data["city"]:
        if address_data["neighborhood"].lower() == address_data["city"].lower():
            address_data["neighborhood"] = None

    location = results["geometry"]["location"]
    return {
        "lat": location["lat"],
        "lng": location["lng"],
        **address_data,
    }


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
        return _parse_address_components(results)

    except Exception as e:
        logger.error(f"Error geocoding address '{address}': {e}")
