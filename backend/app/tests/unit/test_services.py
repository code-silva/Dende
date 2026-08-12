from unittest.mock import patch

from bs4 import BeautifulSoup

from app.services.scraper import _extract_clean_text


def test_extract_clean_text():
    html = """
    <html>
        <head>
            <script>console.log("ignore me");</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>Supermarket</h1>
            <p>Address: Rua 1, Bairro 2</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    text = _extract_clean_text(soup)
    assert "ignore me" not in text
    assert "body { color: red; }" not in text
    assert "Supermarket" in text
    assert "Address: Rua 1, Bairro 2" in text


@patch("app.services.geocoding.requests.get")
def test_geocode_address_success(mock_get):
    from app.services.geocoding import geocode_address

    mock_get.return_value.json.return_value = {
        "status": "OK",
        "results": [
            {
                "geometry": {"location": {"lat": -15.8, "lng": -47.9}},
                "address_components": [
                    {"types": ["administrative_area_level_2"], "long_name": "Brasília"},
                    {"types": ["administrative_area_level_1"], "short_name": "DF"},
                ],
                "formatted_address": "Rua Exemplo, Brasília - DF",
            }
        ],
    }
    mock_get.return_value.raise_for_status.return_value = None

    result = geocode_address("Mercado Exemplo, Rua Exemplo")
    assert result == {
        "lat": -15.8,
        "lng": -47.9,
        "city": "Brasília",
        "state": "DF",
        "formatted_address": "Rua Exemplo, Brasília - DF",
    }


@patch("app.services.ai_extractor.genai.Client")
def test_extract_branches_locations(mock_client):
    from app.services.ai_extractor import extract_branches_locations

    mock_generate = mock_client.return_value.models.generate_content
    mock_generate.return_value.text = '{"branches": [{"address": "Rua Exemplo"}]}'

    result = extract_branches_locations("texto com Rua Exemplo")
    assert result == [{"address": "Rua Exemplo"}]
