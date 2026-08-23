import pytest

from app.models import (
    BranchProductOffer,
    BranchSupermarket,
    Category,
    Offer,
    ParentSupermarket,
    Product,
)
from app.services.ai_extractor import save_extracted_data_to_db


@pytest.mark.django_db
class TestSaveExtractedDataToDB:
    def test_save_and_idempotency(self):
        Category.objects.create(name="Limpeza", priority=1)

        data = {
            "supermarket": "Comper",
            "expiration_date": "2030-12-31",
            "branches": [
                {
                    "lat": -15.0,
                    "lng": -48.0,
                    "city": "Brasília",
                    "state": "DF",
                    "zip_code": "70000000",
                    "street": "Rua X",
                    "number": "S/N",
                    "neighborhood": "Asa Norte",
                }
            ],
            "items": [
                {
                    "name": "Sabão em Pó",
                    "brand": "Omo",
                    "category": "Limpeza",
                    "measurement": 1,
                    "measurement_unit": "kg",
                    "price": 20.50,
                }
            ],
        }

        url = "https://example.com/flyer"

        # First run (Simulation of Celery Task)
        save_extracted_data_to_db(data, url)

        assert ParentSupermarket.objects.filter(name="Comper").exists()
        assert BranchSupermarket.objects.filter(city="Brasília").exists()
        assert Offer.objects.filter(url=url).exists()
        assert Product.objects.filter(name="Sabão em Pó").exists()  # Testing normalization
        assert BranchProductOffer.objects.count() == 1

        # Second run (Idempotency Simulation)
        save_extracted_data_to_db(data, url)

        # Assert no duplicates were created
        assert ParentSupermarket.objects.count() == 1
        assert BranchSupermarket.objects.count() == 1
        assert Offer.objects.count() == 1
        assert Product.objects.count() == 1
        assert BranchProductOffer.objects.count() == 1
