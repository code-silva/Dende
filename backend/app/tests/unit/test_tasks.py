import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry

from app.models import Offer
from app.tasks import (
    extract_supermarket_flyers_data,
    generate_content_with_retry,
    generate_scraping_report,
    scrap_home_page,
    scrap_supermarket_page,
)

FIXTURES_DIRECTORY = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_flyers_directory(tmp_path, monkeypatch):
    """Makes sure to use pytest's 'tmp' directory to prevent host pollution."""
    monkeypatch.setattr("app.tasks.FLYERS_BASE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def home_page_html_content():
    """Returns the home page HTML string content from fixtures."""
    return (FIXTURES_DIRECTORY / "home_page.html").read_text(encoding="utf-8")


@pytest.fixture
def supermarket_page_html_content():
    """Returns the supermarket page HTML string content from fixtures."""
    return (FIXTURES_DIRECTORY / "supermarket_page.html").read_text(encoding="utf-8")


class TestGenerateContentWithRetry:
    """Tests for generate_content_with_retry helper and its tenacity retry behavior."""

    def test_success_on_first_attempt(self):
        """Equivalence partitioning: normal API response without errors."""
        mock_client = MagicMock()
        mock_response = MagicMock(text='{"status": "ok"}')
        mock_client.models.generate_content.return_value = mock_response

        result = generate_content_with_retry(mock_client, "gemini-3.1-flash-lite", ["prompt"])

        assert result == mock_response
        mock_client.models.generate_content.assert_called_once()

    @patch("tenacity.nap.sleep")
    def test_retry_recovery(self, mock_sleep):
        """MC/DC: recovers from a temporary exception on the second attempt."""
        mock_client = MagicMock()
        mock_response = MagicMock(text='{"recovered": true}')
        mock_client.models.generate_content.side_effect = [
            Exception("Temporary network error"),
            mock_response,
        ]

        result = generate_content_with_retry(mock_client, "gemini-3.1-flash-lite", ["prompt"])

        assert result == mock_response
        assert mock_client.models.generate_content.call_count == 2

    @patch("tenacity.nap.sleep")
    def test_max_attempts_exceeded(self, mock_sleep):
        """Boundary value: raises exception after exceeding max retry attempts (stop=5)."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Persistent failure")

        with pytest.raises(Exception, match="Persistent failure"):
            generate_content_with_retry(mock_client, "gemini-3.1-flash-lite", ["prompt"])

        assert mock_client.models.generate_content.call_count == 5


@pytest.mark.django_db
class TestScrapHomePageTask:
    """Tests for the 'scrap_home_page' task."""

    @patch("app.tasks.chord")
    @patch("app.tasks.scrap_supermarket_page.s")
    @patch("app.tasks.requests.get")
    def test_with_real_snapshot(
        self,
        mock_requests_get,
        mock_task_s,
        mock_chord,
        home_page_html_content,
        mock_flyers_directory,
    ):
        """Equivalence partitioning: parses HTML and queues valid supermarket links."""
        mock_response = MagicMock(status_code=200, text=home_page_html_content)
        mock_requests_get.return_value = mock_response

        scrap_home_page()

        assert mock_task_s.call_count > 0
        first_queued_url = mock_task_s.call_args_list[0][0][0]
        assert "encartesdf.com.br" in first_queued_url
        assert mock_chord.call_count == 1

    @patch("app.tasks.logger.info")
    @patch("app.tasks.chord")
    @patch("app.tasks.scrap_supermarket_page.s")
    @patch("app.tasks.requests.get")
    def test_no_active_offers(
        self,
        mock_requests_get,
        mock_task_s,
        mock_chord,
        mock_logger_info,
        mock_flyers_directory,
    ):
        """MC/DC: ignores expired offers (.badge-vencido) and skips chord execution when empty."""
        html_content = """
        <html>
            <h1 class="main-title">
                <a href="https://encartesdf.com.br/expired/">
                    Expired Market <span class="badge-vencido">Vencido</span>
                </a>
            </h1>
        </html>
        """
        mock_requests_get.return_value = MagicMock(status_code=200, text=html_content)

        scrap_home_page()

        assert mock_task_s.call_count == 0
        assert mock_chord.call_count == 0
        mock_logger_info.assert_any_call("No active supermarket offers found to process.")

    @patch("app.tasks.logger.error")
    @patch("app.tasks.requests.get")
    def test_http_exception(self, mock_requests_get, mock_logger_error, mock_flyers_directory):
        """Equivalence partitioning: handles network exceptions gracefully without raising."""
        mock_requests_get.side_effect = Exception("Connection timeout")

        scrap_home_page()

        mock_logger_error.assert_called_once()
        assert (
            "Error when scraping the Home Page: Connection timeout"
            in mock_logger_error.call_args[0][0]
        )


@pytest.mark.django_db
class TestScrapSupermarketPageTask:
    """Tests for the 'scrap_supermarket_page' task."""

    @patch("app.tasks.extract_supermarket_flyers_data.delay")
    @patch("app.tasks.requests.get")
    def test_with_real_snapshot(
        self,
        mock_requests_get,
        mock_extract_delay,
        supermarket_page_html_content,
        mock_flyers_directory,
    ):
        """Equivalence partitioning: downloads images and schedules flyer data extraction."""
        mock_html_response = MagicMock(status_code=200, text=supermarket_page_html_content)
        mock_image_response = MagicMock(status_code=200)
        mock_image_response.iter_content.return_value = [b"fake_image_bytes"]

        def response_router(url_requested, *args, **kwargs):
            if "encartesdf.com.br" in url_requested:
                return mock_html_response
            return mock_image_response

        mock_requests_get.side_effect = response_router

        target_url = "https://encartesdf.com.br/mercado-teste-real/"
        metrics = scrap_supermarket_page(target_url)

        created_dirs = list(mock_flyers_directory.glob("mercado-teste-real_*"))
        assert len(created_dirs) == 1

        temp_folder = created_dirs[0]
        saved_images = list(temp_folder.glob("*.jpg"))
        assert len(saved_images) > 0
        assert mock_extract_delay.call_count == 1
        assert mock_extract_delay.call_args[0][0] == str(temp_folder)
        assert metrics["status"] == "success"
        assert metrics["downloaded_images"] == len(saved_images)

    @patch("app.tasks.requests.get")
    def test_already_processed(self, mock_requests_get, mock_flyers_directory):
        """MC/DC: returns early if supermarket URL already exists in database."""
        target_url = "https://encartesdf.com.br/already-processed/"
        Offer.objects.create(url=target_url, expiration_date=date(2026, 12, 31))

        metrics = scrap_supermarket_page(target_url)

        assert metrics["status"] == "skipped"
        assert metrics["reason"] == "Already processed"
        assert metrics["downloaded_images"] == 0
        assert mock_requests_get.call_count == 0

    @patch("app.tasks.requests.get")
    def test_http_error(self, mock_requests_get, mock_flyers_directory):
        """Equivalence partitioning: returns error status when HTTP request fails."""
        mock_requests_get.side_effect = Exception("HTTP 500 Server Error")

        metrics = scrap_supermarket_page("https://encartesdf.com.br/error/")

        assert metrics["status"] == "error"
        assert "HTTP 500 Server Error" in metrics["reason"]
        assert metrics["downloaded_images"] == 0

    @patch("app.tasks.logger.warning")
    @patch("app.tasks.extract_supermarket_flyers_data.delay")
    @patch("app.tasks.requests.get")
    def test_missing_and_failed_images(
        self,
        mock_requests_get,
        mock_extract_delay,
        mock_logger_warning,
        mock_flyers_directory,
    ):
        """
        Skips missing src attributes
        and individual 404 image failures.
        """

        html_content = """
        <html>
            <div class="text">
                <img class="wp-image-1" />
                <img class="wp-image-2" data-src="https://img.test/01.jpg" />
                <img class="wp-image-3" src="https://img.test/404.jpg" />
            </div>
        </html>
        """
        mock_html = MagicMock(status_code=200, text=html_content)
        mock_img_ok = MagicMock(status_code=200)
        mock_img_ok.iter_content.return_value = [b"img_bytes"]
        mock_img_404 = MagicMock(status_code=404)

        def router(url, *args, **kwargs):
            if "encartesdf" in url:
                return mock_html
            elif "01.jpg" in url:
                return mock_img_ok
            return mock_img_404

        mock_requests_get.side_effect = router

        metrics = scrap_supermarket_page("https://encartesdf.com.br/mixed/")

        assert metrics["status"] == "success"
        assert metrics["downloaded_images"] == 1
        mock_logger_warning.assert_called_once()
        assert (
            "Failed to download image https://img.test/404.jpg"
            in mock_logger_warning.call_args[0][0]
        )


@pytest.mark.django_db
class TestExtractSupermarketFlyersDataTask:
    """Tests for the 'extract_supermarket_flyers_data' task."""

    def test_path_not_found(self, tmp_path):
        """Boundary value: returns error if target directory does not exist."""
        non_existent_folder = tmp_path / "missing_folder"
        result = extract_supermarket_flyers_data(str(non_existent_folder))

        assert result["status"] == "error"
        assert result["reason"] == "Path not found"

    def test_no_images(self, tmp_path):
        """Equivalence partitioning: returns skipped if folder has no valid image extensions."""
        empty_folder = tmp_path / "empty_market"
        empty_folder.mkdir()
        (empty_folder / "doc.pdf").write_text("not an image")

        result = extract_supermarket_flyers_data(str(empty_folder))

        assert result["status"] == "skipped"
        assert result["reason"] == "No images found"

    @patch("app.tasks.genai.Client")
    def test_success(self, mock_genai_client, tmp_path):
        """Equivalence partitioning: extracts flyer data and saves consolidated JSON."""
        market_folder = tmp_path / "test_market"
        market_folder.mkdir()
        (market_folder / "00.jpg").write_bytes(b"fake_img_1")

        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "supermarket": "Test Market",
                "expiration_date": "2026-10-15",
                "items": [{"name": "Rice", "price": 21.90, "type": "Varejo"}],
            }
        )
        mock_client.models.generate_content.return_value = mock_response

        result = extract_supermarket_flyers_data(str(market_folder))

        assert result is None
        output_filepath = market_folder / "extracted_data.json"
        assert output_filepath.exists()

        saved_data = json.loads(output_filepath.read_text(encoding="utf-8"))
        assert saved_data["supermarket"] == "Test Market"
        assert saved_data["expiration_date"] == "2026-10-15"
        assert len(saved_data["items"]) == 1
        assert saved_data["items"][0]["name"] == "Rice"

    @patch("app.tasks.genai.Client")
    def test_multiple_batches_and_consolidation(self, mock_genai_client, tmp_path):
        """Boundary value & MC/DC: splits >15 images into batches and consolidates metadata."""
        market_folder = tmp_path / "batch_market"
        market_folder.mkdir()
        for i in range(16):
            (market_folder / f"{i:02d}.jpg").write_bytes(b"fake_img")

        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client

        resp_batch_1 = MagicMock(
            text=json.dumps(
                {
                    "supermarket": "Main Market",
                    "expiration_date": None,
                    "items": [{"name": "Item 1", "price": 10.0}],
                }
            )
        )
        resp_batch_2 = MagicMock(
            text=json.dumps(
                {
                    "supermarket": "Ignored Market Name",
                    "expiration_date": "2026-11-20",
                    "items": [{"name": "Item 2", "price": 5.0}],
                }
            )
        )
        mock_client.models.generate_content.side_effect = [resp_batch_1, resp_batch_2]

        extract_supermarket_flyers_data(str(market_folder))

        saved_data = json.loads((market_folder / "extracted_data.json").read_text(encoding="utf-8"))
        assert saved_data["supermarket"] == "Main Market"
        assert saved_data["expiration_date"] == "2026-11-20"
        assert len(saved_data["items"]) == 2
        assert mock_client.models.generate_content.call_count == 2

    @patch.object(extract_supermarket_flyers_data, "retry")
    @patch("app.tasks.genai.Client")
    def test_429_per_minute(self, mock_genai_client, mock_retry, tmp_path):
        """MC/DC: retries with 60s delay when HTTP 429 contains 'PerMinute' rate limit error."""
        market_folder = tmp_path / "market_429_min"
        market_folder.mkdir()
        (market_folder / "00.jpg").write_bytes(b"fake_img")

        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        error_429_min = Exception("429 ResourceExhausted: PerMinute rate limit exceeded")
        mock_client.models.generate_content.side_effect = error_429_min
        mock_retry.side_effect = Retry("Re-queued for 60s")

        with pytest.raises(Retry):
            extract_supermarket_flyers_data(str(market_folder))

        mock_retry.assert_called_once_with(exc=error_429_min, countdown=60, max_retries=None)

    @patch.object(extract_supermarket_flyers_data, "retry")
    @patch("app.tasks.genai.Client")
    def test_429_per_day(self, mock_genai_client, mock_retry, tmp_path):
        """MC/DC: retries with 86400s (24h) delay when HTTP 429 daily quota is exceeded."""
        market_folder = tmp_path / "market_429_day"
        market_folder.mkdir()
        (market_folder / "00.jpg").write_bytes(b"fake_img")

        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        error_429_day = Exception("429 ResourceExhausted: PerDay daily quota exceeded")
        mock_client.models.generate_content.side_effect = error_429_day
        mock_retry.side_effect = Retry("Re-queued for 24h")

        with pytest.raises(Retry):
            extract_supermarket_flyers_data(str(market_folder))

        mock_retry.assert_called_once_with(exc=error_429_day, countdown=86400, max_retries=None)

    @patch("app.tasks.genai.Client")
    def test_other_exception(self, mock_genai_client, tmp_path):
        """MC/DC: raises exception directly when error is not an HTTP 429 rate limit."""
        market_folder = tmp_path / "market_500"
        market_folder.mkdir()
        (market_folder / "00.jpg").write_bytes(b"fake_img")

        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("500 Internal Server Error")

        with pytest.raises(Exception, match="500 Internal Server Error"):
            extract_supermarket_flyers_data(str(market_folder))


class TestGenerateScrapingReportTask:
    """Tests for the 'generate_scraping_report' chord callback task."""

    @patch("app.tasks.logger.warning")
    def test_empty_results(self, mock_logger_warning):
        """Equivalence partitioning: logs warning and exits when results list is empty."""
        generate_scraping_report([])
        mock_logger_warning.assert_called_once_with("No scraping results collected for the report.")

    @patch("app.tasks.logger.info")
    @patch("builtins.print")
    def test_mixed_results(self, mock_print, mock_logger_info):
        """Boundary value & MC/DC: aggregates statistics across different task statuses and None."""
        results = [
            {"market": "market-a", "status": "success", "downloaded_images": 12, "reason": ""},
            {
                "market": "market-b",
                "status": "skipped",
                "downloaded_images": 0,
                "reason": "Already processed",
            },
            {"market": "market-c", "status": "error", "downloaded_images": 0, "reason": "Timeout"},
            None,
        ]

        generate_scraping_report(results)

        assert mock_print.call_count == 1
        printed_report = mock_print.call_args[0][0]

        assert "Total Establishments Evaluated: 4" in printed_report
        assert "Supermarkets Processed Successfully: 1" in printed_report
        assert "Supermarkets Skipped (Existing Data): 1" in printed_report
        assert "Supermarkets with Execution Errors: 1" in printed_report
        assert "Total Images/Flyers Downloaded: 12" in printed_report
        mock_logger_info.assert_called_once_with("Scraping workflow completed execution.")
