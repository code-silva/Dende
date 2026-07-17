from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from app.models import BranchProductOffer, BranchSupermarket, ParentSupermarket

# Sqlite doesn't support composite unique contraint.
# So I had to remove it from testing
if hasattr(BranchSupermarket._meta, "constraints"):
    BranchSupermarket._meta.constraints = [
        c
        for c in BranchSupermarket._meta.constraints
        if c.name != "unique_coordinates_parent_supermarket"
    ]


@pytest.fixture(autouse=True)
def register_gis_generator():
    baker.generators.add("django.contrib.gis.db.models.fields.PointField", lambda: Point(0, 0))


@pytest.fixture
def api_client():
    """Fixture to provide the DRF client."""
    return APIClient()


@pytest.fixture
def parent_supermarket(db):
    return baker.make(ParentSupermarket, name="Super Market")


@pytest.fixture
def branch_supermarket(db, parent_supermarket):
    """Creates a branch store at a specific coordinate and links an offer to it."""
    branch = baker.make(
        BranchSupermarket,
        parent_supermarket=parent_supermarket,
        state="DF",
        city="Gama",
        address="Gama Sul, QI 01",
        coordinates=Point(-47.9292, -15.7801),
    )

    future_date = timezone.now().date() + timedelta(days=1)
    baker.make(BranchProductOffer, branch_supermarket=branch, offer__expiration_date=future_date)

    return branch


@pytest.fixture
def supermarkets_list(db):
    """Creates multiple supermarkets to test sorting and filters, with offers linked."""

    future_date = timezone.now().date() + timedelta(days=1)
    parent_supermarkets = baker.make(ParentSupermarket, _quantity=5)
    branch_supermarkets = []

    for parent in parent_supermarkets:
        branch = baker.make(
            BranchSupermarket,
            parent_supermarket=parent,
            state="DF",
            city="Gama",
            address="Gama Sul",
        )
        baker.make(
            BranchProductOffer, branch_supermarket=branch, offer__expiration_date=future_date
        )

        branch_supermarkets.append(branch)

    branch_supermarkets.sort(key=lambda x: x.parent_supermarket.name)

    return branch_supermarkets


@pytest.fixture
def offers_list(db, parent_supermarket):
    """
    Returns an offers list for testing (from BracnProductOffer model).
    """

    category1 = baker.make("app.Category", priority=1)
    category2 = baker.make("app.Category", priority=2)
    category3 = baker.make("app.Category", priority=3)

    offers = [
        baker.make(
            BranchProductOffer,
            product__name="arroz",
            product__category=category1,
            branch_supermarket__parent_supermarket=parent_supermarket,
            branch_supermarket__state="DF",
            branch_supermarket__city="Gama",
            branch_supermarket__address="Gama Sul, QI 01",
            branch_supermarket__coordinates=Point(-47.9292, -15.7801, srid=4326),
        ),
        baker.make(
            BranchProductOffer,
            product__name="feijão",
            product__category=category2,
            branch_supermarket__parent_supermarket=parent_supermarket,
            branch_supermarket__state="DF",
            branch_supermarket__city="Gama",
            branch_supermarket__address="Gama Sul, QI 01",
            branch_supermarket__coordinates=Point(-47.9292, -15.7801, srid=4326),
        ),
        baker.make(
            BranchProductOffer,
            product__name="danone",
            product__category=category3,
            branch_supermarket__parent_supermarket=parent_supermarket,
            branch_supermarket__state="DF",
            branch_supermarket__city="Gama",
            branch_supermarket__address="Gama Sul, QI 01",
            branch_supermarket__coordinates=Point(-47.9292, -15.7801, srid=4326),
        ),
    ]

    offers.sort(key=lambda x: x.product.category.priority)
    return offers


@pytest.fixture
def branch_with_active_offers(db):
    """Creates a branch with only active (non-expired) offers."""
    parent = baker.make(ParentSupermarket, name="Active Market")
    branch = baker.make(
        BranchSupermarket,
        parent_supermarket=parent,
        state="DF",
        city="Gama",
        address="Gama Sul, QI 02",
        coordinates=Point(-47.9292, -15.7801),
    )
    future_date = timezone.now().date() + timedelta(days=5)
    baker.make(
        BranchProductOffer,
        branch_supermarket=branch,
        offer__expiration_date=future_date,
        _quantity=2,
    )
    return branch


@pytest.fixture
def branch_with_expired_offers(db):
    """Creates a branch with only expired offers."""
    parent = baker.make(ParentSupermarket, name="Expired Market")
    branch = baker.make(
        BranchSupermarket,
        parent_supermarket=parent,
        state="DF",
        city="Gama",
        address="Gama Sul, QI 03",
        coordinates=Point(-47.9292, -15.7801),
    )
    past_date = timezone.now().date() - timedelta(days=1)
    baker.make(
        BranchProductOffer,
        branch_supermarket=branch,
        offer__expiration_date=past_date,
        _quantity=2,
    )
    return branch


@pytest.fixture
def branch_with_mixed_offers(db):
    """Creates a branch with both active and expired offers."""
    parent = baker.make(ParentSupermarket, name="Mixed Market")
    branch = baker.make(
        BranchSupermarket,
        parent_supermarket=parent,
        state="DF",
        city="Gama",
        address="Gama Sul, QI 04",
        coordinates=Point(-47.9292, -15.7801),
    )
    future_date = timezone.now().date() + timedelta(days=5)
    past_date = timezone.now().date() - timedelta(days=1)
    baker.make(
        BranchProductOffer,
        branch_supermarket=branch,
        offer__expiration_date=future_date,
    )
    baker.make(
        BranchProductOffer,
        branch_supermarket=branch,
        offer__expiration_date=past_date,
    )
    return branch
