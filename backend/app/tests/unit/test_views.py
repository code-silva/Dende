from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from app.models import BranchProductOffer, BranchSupermarket, ParentSupermarket


@pytest.mark.django_db
class TestBranchSupermarketListView:
    """
    Class destined to the elaboration of tests of 'BranchSupermarketListView' view.
    """

    URL = reverse("nearby_markets")

    @pytest.mark.parametrize("value", [" ", "", "invalidtype", 123131.13131313, True])
    def test_with_invalid_longitude(self, value, api_client, supermarkets_list):
        """
        Testing when longitude is invalid.
        It should return an ordered supermarket list.
        """

        response = api_client.get(
            self.URL,
            {
                "latitude": -15.32,
                "longitude": value,
            },
        )

        results = response.data["results"]

        for index in range(len(results)):
            supermarket_name = results[index]["name"]
            assert supermarket_name == supermarkets_list[index].parent_supermarket.name

    @pytest.mark.parametrize("value", [" ", "", "invalidtype", 123131.13131313, True])
    def test_with_invalid_latitude(self, value, api_client, supermarkets_list):
        """
        Testing when latitude is invalid.
        It should return an ordered supermarket list.
        """

        response = api_client.get(
            self.URL,
            {
                "latitude": value,
                "longitude": -15.32,
            },
        )

        results = response.data["results"]

        for index in range(len(results)):
            supermarket_name = results[index]["name"]
            assert supermarket_name == supermarkets_list[index].parent_supermarket.name

    def test_with_user_outside_radius(self, api_client):
        """
        Testing when the user is not within determined radius.
        It should return an empty list.
        """

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": -47.9292})

        results = response.data["results"]
        assert not results

    def test_with_user_inside_radius(self, api_client, branch_supermarket):
        """
        Testing when the user is within determined radius.
        It should return the supermarkets close to the user.
        """

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": -47.9292})

        results = response.data["results"]

        assert len(results) == 1
        assert results[0]["name"] == branch_supermarket.parent_supermarket.name

    def test_market_with_only_active_offers(self, api_client, branch_with_active_offers):
        """
        Testing that a market with only active (non-expired) offers appears in the response.
        """

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": -47.9292})

        results = response.data["results"]
        names = [result["name"] for result in results]

        assert branch_with_active_offers.parent_supermarket.name in names

    def test_market_with_only_expired_offers(self, api_client, branch_with_expired_offers):
        """
        Testing that a market with only expired offers does NOT appear in the response.
        """

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": -47.9292})

        results = response.data["results"]
        names = [result["name"] for result in results]

        assert branch_with_expired_offers.parent_supermarket.name not in names

    def test_market_with_mixed_offers(self, api_client, branch_with_mixed_offers):
        """
        Testing that a market with mixed (active and expired) offers appears in the response.
        """

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": -47.9292})

        results = response.data["results"]
        names = [result["name"] for result in results]

        assert branch_with_mixed_offers.parent_supermarket.name in names

    def test_returns_markets_beyond_default_radius(self, api_client, db):
        """
        Testing that all active markets are returned ordered by distance,
        regardless of distance, when no radiusInKm is provided.
        """

        future_date = timezone.now().date() + timedelta(days=1)
        for name, longitude, latitude in [
            ("Near", -47.9292, -15.7801),
            ("Far", -47.8, -16.0),
        ]:
            parent = baker.make(ParentSupermarket, name=name)
            branch = baker.make(
                BranchSupermarket,
                parent_supermarket=parent,
                state="DF",
                city="Gama",
                address=f"{name}, QI 01",
                coordinates=Point(longitude, latitude, srid=4326),
            )
            baker.make(
                BranchProductOffer,
                branch_supermarket=branch,
                offer__expiration_date=future_date,
            )

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": -47.9292})

        results = response.data["results"]
        names = [result["name"] for result in results]

        assert names == ["Near", "Far"]

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    def test_city_filter_is_case_and_accent_insensitive(self, api_client, db):
        """
        Testing that the city filter matches case and accent variations
        (e.g. 'taguaTINGA' finds markets in 'Taguatinga').
        """

        future_date = timezone.now().date() + timedelta(days=1)
        for name, city in [
            ("Atacadão Taguatinga", "Taguatinga"),
            ("Comper Gama", "Gama"),
        ]:
            parent = baker.make(ParentSupermarket, name=name)
            branch = baker.make(
                BranchSupermarket,
                parent_supermarket=parent,
                state="DF",
                city=city,
                address=f"{name}, QI 01",
                coordinates=Point(-47.9292, -15.7801, srid=4326),
            )
            baker.make(
                BranchProductOffer,
                branch_supermarket=branch,
                offer__expiration_date=future_date,
            )

        response = api_client.get(
            self.URL,
            {
                "latitude": -15.7801,
                "longitude": -47.9292,
                "city": "taguaTINGA",
            },
        )

        results = response.data["results"]
        names = [result["name"] for result in results]

        assert names == ["Atacadão Taguatinga"]

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    @pytest.mark.parametrize(
        "query, expected_name",
        [
            ("conper", "Comper"),  # letter substitution
            ("commper", "Comper"),  # extra character insertion
            ("primavrea", "Primavera"),  # adjacent transposition
            ("primvera", "Primavera"),  # character omission
            ("pao", "Pão"),  # missing accent
        ],
    )
    def test_address_search_tolerates_typos(self, api_client, db, query, expected_name):
        """
        Testing that the fuzzy search (pg_trgm) tolerates small typos and
        accent variations when searching markets by name/address.
        """

        future_date = timezone.now().date() + timedelta(days=1)
        for name in ["Comper", "Primavera", "Ponto Alto", "Extra"]:
            parent = baker.make(ParentSupermarket, name=name)
            branch = baker.make(
                BranchSupermarket,
                parent_supermarket=parent,
                state="DF",
                city="Gama",
                address=f"{name}, QI 01",
                coordinates=Point(-47.9292, -15.7801, srid=4326),
            )
            baker.make(
                BranchProductOffer,
                branch_supermarket=branch,
                offer__expiration_date=future_date,
            )

        response = api_client.get(
            self.URL,
            {"latitude": -15.7801, "longitude": -47.9292, "address": query},
        )

        names = [result["name"] for result in response.data["results"]]

        assert expected_name in names

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    def test_address_search_rejects_unrelated_terms(self, api_client, db):
        """
        Testing that completely unrelated strings (e.g. 'xyzabc') do not
        produce false positives in the fuzzy market search.
        """

        future_date = timezone.now().date() + timedelta(days=1)
        parent = baker.make(ParentSupermarket, name="Comper")
        branch = baker.make(
            BranchSupermarket,
            parent_supermarket=parent,
            state="DF",
            city="Gama",
            address="Comper, QI 01",
            coordinates=Point(-47.9292, -15.7801, srid=4326),
        )
        baker.make(
            BranchProductOffer,
            branch_supermarket=branch,
            offer__expiration_date=future_date,
        )

        response = api_client.get(
            self.URL,
            {"latitude": -15.7801, "longitude": -47.9292, "address": "xyzabc"},
        )

        assert not response.data["results"]

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    def test_address_search_orders_by_relevance(self, api_client, db):
        """
        Testing that fuzzy results are ordered by similarity relevance,
        with the most similar market appearing first.
        """

        future_date = timezone.now().date() + timedelta(days=1)
        for name in ["Comper", "Compre Bem", "Extra"]:
            parent = baker.make(ParentSupermarket, name=name)
            branch = baker.make(
                BranchSupermarket,
                parent_supermarket=parent,
                state="DF",
                city="Gama",
                address=f"{name}, QI 01",
                coordinates=Point(-47.9292, -15.7801, srid=4326),
            )
            baker.make(
                BranchProductOffer,
                branch_supermarket=branch,
                offer__expiration_date=future_date,
            )

        response = api_client.get(
            self.URL,
            {"latitude": -15.7801, "longitude": -47.9292, "address": "comper"},
        )

        results = response.data["results"]

        assert results
        assert results[0]["name"] == "Comper"


@pytest.mark.django_db
class TestBranchCityListView:
    """
    Class destined to the elaboration of tests of 'BranchCityListView' view.
    """

    URL = reverse("cities_list")

    def test_returns_empty_when_no_active_offers(self, api_client, branch_with_expired_offers):
        """
        Testing that no cities are returned when there are no active offers.
        """

        response = api_client.get(self.URL)

        assert response.status_code == 200
        assert response.data == []

    def test_returns_distinct_active_cities_ordered(self, api_client, db):
        """
        Testing that only unique cities of markets with active offers are
        returned, ordered alphabetically and without duplicates.
        """

        future_date = timezone.now().date() + timedelta(days=1)

        for name, city in [
            ("Mercado A", "Taguatinga"),
            ("Mercado B", "Brasília"),
            ("Mercado C", "Gama"),
            ("Mercado D", "Taguatinga"),
        ]:
            parent = baker.make(ParentSupermarket, name=name)
            branch = baker.make(
                BranchSupermarket,
                parent_supermarket=parent,
                state="DF",
                city=city,
                address="QI 01",
            )
            baker.make(
                BranchProductOffer,
                branch_supermarket=branch,
                offer__expiration_date=future_date,
            )

        response = api_client.get(self.URL)

        assert response.status_code == 200
        assert response.data == ["Brasília", "Gama", "Taguatinga"]

    def test_excludes_cities_with_only_expired_offers(self, api_client, db):
        """
        Testing that cities of markets with only expired offers are not included.
        """

        future_date = timezone.now().date() + timedelta(days=1)
        past_date = timezone.now().date() - timedelta(days=1)

        active_parent = baker.make(ParentSupermarket, name="Ativo")
        active_branch = baker.make(
            BranchSupermarket,
            parent_supermarket=active_parent,
            state="DF",
            city="Gama",
            address="QI 01",
        )
        baker.make(
            BranchProductOffer,
            branch_supermarket=active_branch,
            offer__expiration_date=future_date,
        )

        expired_parent = baker.make(ParentSupermarket, name="Expirado")
        expired_branch = baker.make(
            BranchSupermarket,
            parent_supermarket=expired_parent,
            state="DF",
            city="Taguatinga",
            address="QI 02",
        )
        baker.make(
            BranchProductOffer,
            branch_supermarket=expired_branch,
            offer__expiration_date=past_date,
        )

        response = api_client.get(self.URL)

        assert response.status_code == 200
        assert response.data == ["Gama"]


@pytest.mark.django_db
class TestHybridSearchView:
    """
    Class destined to the elaboration of tests of 'HybridSearchView' view.
    """

    URL = reverse("search")

    @pytest.mark.parametrize("value", ["", "    "])
    @pytest.mark.parametrize("scope", [None, "products"])
    def test_get_with_invalid_query(self, value, scope, api_client):
        """
        Testing the GET method of the view with an invalid query (empty or '').
        It should return an empty offers array regardless of the scope.
        """

        params = {"query": value}
        if scope:
            params["scope"] = scope

        response = api_client.get(self.URL, params)

        results = response.data["offers"]

        assert response.status_code == 200
        assert not results

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    @pytest.mark.parametrize("value", ["arroz", "feijão", "danone"])
    def test_get_with_valid_query(self, value, api_client, offers_list):
        """
        Testing the GET method of the view with a valid query.
        It should return the fetched products.
        """

        response = api_client.get(self.URL, {"query": value})

        results = response.data["offers"]

        assert response.status_code == 200
        assert results == offers_list

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    @pytest.mark.parametrize("value", ["feijao", "sabao"])
    def test_get_with_valid_query_scope_products_unaccent(self, value, api_client, offers_list):
        """
        Testing the scope=products behavior with de-accented queries.
        It should still find accented products like 'Feijão'.
        """

        response = api_client.get(self.URL, {"query": value, "scope": "products"})

        results = response.data["offers"]

        assert response.status_code == 200
        assert len(results) > 0

    @pytest.mark.skip(reason="PostgreeSQL is needed to run this test.")
    def test_get_scope_products_fuzzy_typo(self, api_client, offers_list):
        """
        Testing that scope=products tolerates small typos via trigram similarity.
        'arroz' should still be found even if typed as 'arroz' or close variants.
        """

        response = api_client.get(self.URL, {"query": "aroz", "scope": "products"})

        results = response.data["offers"]

        assert response.status_code == 200
        assert any("arroz" in offer["productName"].lower() for offer in results)


@pytest.mark.django_db
class TestBranchProductOfferListView:
    """
    Class destined to the elaboration of tests of 'BranchProductOfferListView' view.
    """

    URL = reverse("offers_list")

    def test_with_all_fields_informed(self, api_client, offers_list):
        """
        Testing when everything (latitude, longitude, supermarket_id) was informed.
        It should return a list of offers ordered by the 'category' priority,
        and of only the informed supermarket.
        """

        supermarket_id = offers_list[0].branch_supermarket.id
        supermarket_name = offers_list[0].branch_supermarket.parent_supermarket.name

        response = api_client.get(
            self.URL,
            {"latitude": -15.7801, "longitude": -47.9292, "marketId": supermarket_id},
        )

        results = response.data["results"]
        priority_map = {offer.id: offer.product.category.priority for offer in offers_list}
        priorities = [priority_map[offer["id"]] for offer in results]

        assert response.status_code == 200
        assert priorities == sorted(priorities)

        for result in results:
            assert supermarket_name == result["marketName"]

    def test_with_supermarket_id_missing(self, api_client, offers_list):
        """
        Testing when everything (latitude, longitude) but the supermarket_identifier was informed.
        It should return a list of offers ordered by the 'category' priority.
        """

        response = api_client.get(
            self.URL,
            {
                "latitude": -15.7801,
                "longitude": -47.9292,
            },
        )

        results = response.data["results"]
        priority_map = {offer.id: offer.product.category.priority for offer in offers_list}
        priorities = [priority_map[offer["id"]] for offer in results]

        assert response.status_code == 200
        assert priorities == sorted(priorities)

    @pytest.mark.parametrize("value", [" ", "", "invalidtype", 123131.13131313, True])
    def test_with_invalid_longitude(self, value, api_client, offers_list):
        """
        Testing when longitude is invalid.
        It should return a list of offers ordered by the 'category' priority.
        """

        response = api_client.get(self.URL, {"latitude": -15.7801, "longitude": value})

        results = response.data["results"]
        priority_map = {offer.id: offer.product.category.priority for offer in offers_list}
        priorities = [priority_map[offer["id"]] for offer in results]

        assert response.status_code == 200
        assert priorities == sorted(priorities)

    @pytest.mark.parametrize("value", [" ", "", "invalidtype", 123131.13131313, True])
    def test_with_invalid_latitude(self, value, api_client, offers_list):
        """
        Testing when latitude is invalid.
        It should return a list of offers ordered by the 'category' priority.
        """

        response = api_client.get(self.URL, {"latitude": value, "longitude": -47.9292})

        results = response.data["results"]
        priority_map = {offer.id: offer.product.category.priority for offer in offers_list}
        priorities = [priority_map[offer["id"]] for offer in results]

        assert response.status_code == 200
        assert priorities == sorted(priorities)

    def test_with_user_outside_radius(self, api_client, offers_list):
        """
        Testing when the user is not within determined radius.
        It should return an empty list.
        """

        supermarket_id = offers_list[0].branch_supermarket.id

        response = api_client.get(
            self.URL, {"latitude": -78.543, "longitude": -1.213, "supermarket_id": supermarket_id}
        )
        results = response.data["results"]
        assert not results
