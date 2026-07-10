from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tasks import extract_supermarket_flyers_data, scrap_home_page, scrap_supermarket_page

FIXTURES_DIRECTORY = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_flyers_directory(tmp_path, monkeypatch):
    """
    Makes sure to use the 'tmp' directory from pytest, so that it is cleaned
    automatically after testing, preventing host machine pollution.
    """
    monkeypatch.setattr("app.tasks.FLYERS_BASE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def home_page_html_content():
    """
    Returns the home page HTML string content, read from the fixtures/home_page.html file.
    """
    return (FIXTURES_DIRECTORY / "home_page.html").read_text(encoding="utf-8")


@pytest.fixture
def supermarket_page_html_content():
    """
    Returns the supermarket page HTML string content,
    read from the fixtures/supermarket_page.html file.
    """
    return (FIXTURES_DIRECTORY / "supermarket_page.html").read_text(encoding="utf-8")


@pytest.mark.django_db
class TestScrapHomePageTask:
    """
    Class destined to the elaboration of tests of the 'scrap_home_page' task.
    """

    @patch("app.tasks.chord")
    @patch("app.tasks.scrap_supermarket_page.s")
    @patch("app.tasks.requests.get")
    def test_scrap_home_page_with_real_snapshot(
        self,
        mock_requests_get,
        mock_task_s,
        mock_chord,
        home_page_html_content,
        mock_flyers_directory,
    ):
        """
        Testing the home page scraping logic using a real HTML snapshot.
        It should parse the HTML correctly and queue the valid supermarkets using signatures.
        """

        mocked_response = MagicMock()
        mocked_response.status_code = 200
        mocked_response.text = home_page_html_content
        mock_requests_get.return_value = mocked_response

        scrap_home_page()

        assert mock_task_s.call_count > 0
        first_queued_url = mock_task_s.call_args_list[0][0][0]
        assert "encartesdf.com.br" in first_queued_url
        assert mock_chord.call_count == 1


@pytest.mark.django_db
class TestScrapSupermarketPageTask:
    """
    Class destined to the elaboration of tests of the 'scrap_supermarket_page' task.
    """

    @patch("app.tasks.extract_supermarket_flyers_data.delay")
    @patch("app.tasks.requests.get")
    def test_scrap_supermarket_page_with_real_snapshot(
        self,
        mock_requests_get,
        mock_extract_delay,
        supermarket_page_html_content,
        mock_flyers_directory,
    ):
        """
        Testing the supermarket page scraping logic using a real HTML snapshot.
        It should mock the image downloading and save the files in the temporary directory.
        """

        mocked_html_response = MagicMock()
        mocked_html_response.status_code = 200
        mocked_html_response.text = supermarket_page_html_content

        mocked_image_response = MagicMock()
        mocked_image_response.status_code = 200
        mocked_image_response.iter_content.return_value = [b"fake_image_bytes"]

        def mocked_response_router(url_requested, *arguments, **keyword_arguments):
            """
            Routes the mocked response based on the requested URL string.
            Returns the HTML object for the main page and the bytes object for the image sources.
            """

            if "encartesdf.com.br" in url_requested:
                return mocked_html_response

            return mocked_image_response

        mock_requests_get.side_effect = mocked_response_router

        supermarket_target_url = "https://encartesdf.com.br/mercado-teste-real/"

        scrap_supermarket_page(supermarket_target_url)

        # Verifying if the directory was created successfully by the task
        created_directories = list(mock_flyers_directory.glob("mercado-teste-real_*"))
        assert len(created_directories) == 1

        temporary_folder = created_directories[0]
        saved_image_files = list(temporary_folder.glob("*.jpg"))
        assert len(saved_image_files) > 0
        assert mock_extract_delay.call_count == 1
        assert mock_extract_delay.call_args[0][0] == str(temporary_folder)


@pytest.mark.django_db
class TestExtractSupermarketFlyersDataTask:
    """
    Class destined to the elaboration of tests of the 'extract_supermarket_flyers_data' task.
    """

    @patch("app.tasks.genai.Client")
    def test_extract_supermarket_flyers_data_success(self, mock_genai_client, tmp_path):
        """
        Testing flyer extraction from a market folder sending up to 5 images per request.
        """
        market_folder = tmp_path / "mercado_teste"
        market_folder.mkdir()
        (market_folder / "00.jpg").write_bytes(b"fake_img_1")
        (market_folder / "01.jpg").write_bytes(b"fake_img_2")

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        mock_response = MagicMock()
        mock_response.text = (
            '{"supermarket": "Mercado Teste", "expiration_date": "2026-10-15",'
            ' "items": [{"name": "Arroz", "price": 21.90}]}'
        )
        mock_client_instance.models.generate_content.return_value = mock_response

        result = extract_supermarket_flyers_data(str(market_folder), url="https://teste.com")

        assert result["status"] == "success"
        assert len(result["extracted_batches"]) == 1
        assert result["extracted_batches"][0]["model_used"] == "gemini-2.5-flash"
        assert result["extracted_batches"][0]["data"]["supermarket"] == "Mercado Teste"

    @patch("app.tasks.genai.Client")
    def test_extract_supermarket_flyers_data_429_rotation(self, mock_genai_client, tmp_path):
        """
        Testing rotation across free models when HTTP 429 quota exceeded error happens.
        """
        market_folder = tmp_path / "mercado_429"
        market_folder.mkdir()
        (market_folder / "00.jpg").write_bytes(b"fake_img")

        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance

        error_429 = Exception("429 ResourceExhausted: Quota exceeded")
        error_429.code = 429

        mock_response = MagicMock()
        mock_response.text = (
            '{"supermarket": "Mercado 429", "expiration_date": "2026-10-15",'
            ' "items": [{"name": "Feijao", "price": 8.90}]}'
        )

        mock_client_instance.models.generate_content.side_effect = [error_429, mock_response]

        result = extract_supermarket_flyers_data(str(market_folder))

        assert result["status"] == "success"
        assert result["extracted_batches"][0]["model_used"] == "gemini-2.0-flash"
