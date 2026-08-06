import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from google.genai import errors as genai_errors
from pydantic import ValidationError

from app.models import Offer
from app.tasks import (
    _handle_extraction_error,
    extract_supermarket_flyers_data,
    scrap_home_page,
    scrap_supermarket_page,
)


# Mocked task instance for retries
class MockTaskInstance:
    def retry(self, exc=None, countdown=None, max_retries=None):
        return Retry(f"Retrying: {exc}")


@pytest.fixture
def mock_task():
    return MockTaskInstance()


@pytest.mark.django_db
class TestScrapHomePageBusinessRules:
    """MC/DC Tests for scrap_home_page business rules."""

    @patch("app.tasks.get_active_supermarkets")
    @patch("app.tasks.scrap_supermarket_page.delay")
    def test_dispatches_task_for_each_active_supermarket(self, mock_delay, mock_get_active):
        """Rule: Every active supermarket link triggers an asynchronous scraping sub-task."""
        mock_get_active.return_value = ["url1", "url2", "url3"]
        scrap_home_page()
        assert mock_delay.call_count == 3
        mock_delay.assert_any_call("url1")
        mock_delay.assert_any_call("url2")
        mock_delay.assert_any_call("url3")

    @patch("app.tasks.get_active_supermarkets")
    @patch("app.tasks.logger.error")
    def test_handles_scraping_failures_gracefully(self, mock_logger, mock_get_active):
        """Rule: Connection or parsing errors shouldn't crash the orchestrator."""
        mock_get_active.side_effect = Exception("Target site is down")
        scrap_home_page()
        mock_logger.assert_called_once()
        assert "Target site is down" in mock_logger.call_args[0][0]


@pytest.mark.django_db
class TestScrapSupermarketPageBusinessRules:
    """MC/DC Tests for scrap_supermarket_page business rules."""

    @patch("app.tasks.logger.info")
    def test_skips_processing_if_offer_already_exists(self, mock_logger):
        """Rule: Avoid duplicate AI processing and DB insertion for already processed URLs."""
        url = "http://test.com/promo"
        Offer.objects.create(url=url, expiration_date=date(2026, 12, 31))

        scrap_supermarket_page(url)
        mock_logger.assert_called_with(f"Skipping {url}: Already processed.")

    @patch("app.tasks.download_supermarket_flyers")
    @patch("app.tasks.extract_supermarket_flyers_data.delay")
    def test_aborts_extraction_if_no_images_downloaded(self, mock_extract, mock_download):
        """Rule: Do not trigger costly AI extraction if image download failed (count = 0)."""
        url = "http://test.com/promo"
        mock_download.return_value = ("/fake/path", 0)  # 0 images downloaded
        scrap_supermarket_page(url)
        mock_extract.assert_not_called()

    @patch("app.tasks.download_supermarket_flyers")
    @patch("app.tasks.extract_supermarket_flyers_data.delay")
    def test_dispatches_ai_extraction_on_successful_download(self, mock_extract, mock_download):
        """Rule: Triggers AI extraction with local folder path and URL if images exist."""
        url = "http://test.com/promo"
        mock_download.return_value = ("/fake/path", 5)  # 5 images downloaded
        scrap_supermarket_page(url)
        mock_extract.assert_called_once_with("/fake/path", url)


@pytest.mark.django_db
class TestExtractSupermarketFlyersDataBusinessRules:
    """MC/DC Tests for AI data extraction orchestrator rules."""

    @patch("app.tasks.get_flyer_images")
    def test_aborts_if_no_images_found_in_folder(self, mock_get_images):
        """Rule: Validation block to prevent crashing on empty directories."""
        mock_get_images.return_value = []
        result = extract_supermarket_flyers_data("/fake", "http://test.com")
        assert result["status"] == "skipped"

    @patch("app.tasks.genai.Client")
    @patch("app.tasks.get_flyer_images")
    @patch("app.tasks.process_flyers_batch")
    @patch("app.tasks.save_extracted_data")
    @patch("app.tasks.save_extracted_data_to_db")
    def test_orchestrates_extraction_flow_and_saves_to_db(
        self, mock_save_db, mock_save_json, mock_process, mock_get_images, mock_client
    ):
        """Rule: Successfully process, consolidate, save JSON locally and persist to Database."""
        # Mock 2 images, enough for 1 batch
        mock_get_images.return_value = [Path("/fake/1.jpg"), Path("/fake/2.jpg")]

        # Mock the AI processing return
        mock_process.return_value = {
            "supermarket": "Test Market",
            "expiration_date": "2026-10-10",
            "items": [{"name": "Arroz", "brand": "Camil", "price": 20.0}],
        }

        result = extract_supermarket_flyers_data("/fake", "http://url.com")

        assert result["status"] == "success"
        # Verify it attempted to save to DB passing the URL
        mock_save_db.assert_called_once()
        assert mock_save_db.call_args[0][1] == "http://url.com"
        # Verify JSON was saved
        mock_save_json.assert_called_once()


class TestHandleExtractionErrorBusinessRules:
    """MC/DC Tests for the Retry and Error Handling rules during AI extraction."""

    def test_retry_on_pydantic_validation_error(self, mock_task):
        """Rule: Retries after 30s if AI outputs invalid JSON (Pydantic ValidationError)."""
        error = ValidationError.from_exception_data(title="Test", line_errors=[])
        with pytest.raises(Retry):
            _handle_extraction_error(mock_task, error, "/fake")

    def test_retry_on_json_decode_error(self, mock_task):
        """Rule: Retries after 30s if AI outputs broken JSON string."""
        error = json.JSONDecodeError("Expecting value", "", 0)
        with pytest.raises(Retry):
            _handle_extraction_error(mock_task, error, "/fake")

    def test_retry_on_api_rate_limit(self, mock_task):
        """Rule: Retries after 60s if hitting Gemini short burst limit (429 PerMinute)."""
        error = genai_errors.ClientError(
            code=429, response_json={"error": {"message": "PerMinute rate limit exceeded"}}
        )
        with pytest.raises(Retry):
            _handle_extraction_error(mock_task, error, "/fake")

    def test_retry_on_api_daily_quota(self, mock_task):
        """Rule: Retries after 24h if hitting Gemini daily quota (429 PerDay)."""
        error = genai_errors.ClientError(
            code=429, response_json={"error": {"message": "PerDay daily quota exceeded"}}
        )
        with pytest.raises(Retry):
            _handle_extraction_error(mock_task, error, "/fake")

    def test_fail_fast_on_unknown_errors(self, mock_task):
        """Rule: Non-recoverable errors (e.g. OS errors) crash the task directly."""
        error = Exception("Unexpected OS Error")
        with pytest.raises(Exception, match="Unexpected OS Error"):
            _handle_extraction_error(mock_task, error, "/fake")
