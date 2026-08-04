from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, Q
from django.db.models.functions import Greatest
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BranchProductOffer, BranchSupermarket
from .pagination import BranchSupermarketPagination, OffersPagination
from .serializers import (
    BranchProductOfferSerializer,
    BranchSupermarketSerializer,
)
from .utils import normalize_search_query


class HybridSearchView(APIView):
    """
    View responsible for performing a unified search across both product offers and
    supermarkets. It uses trigram similarity and text filtering to find relevant
    results based on names, brands, or categories.

    Query params:
      - query: search term (required). It is trimmed, lowercased and accent-stripped
        before matching so that "feijao" finds "Feijão" and "sabao" finds "Sabão".
      - scope: when "products", applies the accent-insensitive fuzzy ranking tuned
        for the product search on the Supermarkets screen. Other consumers of this
        endpoint (home, search results) keep the legacy behavior by default.
    """

    SIMILARITY_THRESHOLD = 0.25

    def get(self, request):
        query = normalize_search_query(request.GET.get("query", ""))
        scope = request.GET.get("scope")

        if not query:
            return Response({"offers": []})

        offers = self._search_products(query) if scope == "products" else self._search_legacy(query)

        return Response({"offers": BranchProductOfferSerializer(offers, many=True).data})

    def _search_products(self, query):
        """
        Accent-insensitive trigram search ordered by combined relevance.
        Uses Unaccent() on the indexed fields so accented values ("Feijão")
        reach high similarity against de-accented queries ("feijao").
        """
        return (
            BranchProductOffer.objects.annotate(
                similarity_name=TrigramSimilarity(Unaccent("product__name"), query),
                similarity_brand=TrigramSimilarity(Unaccent("product__brand"), query),
                relevance=Greatest(F("similarity_name"), F("similarity_brand")),
            )
            .filter(
                Q(product__name__unaccent__icontains=query)
                | Q(product__brand__unaccent__icontains=query)
                | Q(product__category__name__unaccent__icontains=query)
                | Q(similarity_name__gt=self.SIMILARITY_THRESHOLD)
                | Q(similarity_brand__gt=self.SIMILARITY_THRESHOLD)
            )
            .select_related(
                "product",
                "product__category",
                "branch_supermarket__parent_supermarket",
            )
            .order_by("-relevance", "-similarity_name")
        )

    def _search_legacy(self, query):
        """Keeps the original behavior for consumers that do not pass scope=products."""
        return (
            BranchProductOffer.objects.annotate(
                similarity_name=TrigramSimilarity("product__name", query),
                similarity_brand=TrigramSimilarity("product__brand", query),
            )
            .filter(
                Q(product__name__unaccent__icontains=query)
                | Q(product__brand__unaccent__icontains=query)
                | Q(product__category__name__unaccent__icontains=query)
                | Q(similarity_name__gt=self.SIMILARITY_THRESHOLD)
                | Q(similarity_brand__gt=self.SIMILARITY_THRESHOLD)
            )
            .select_related(
                "product",
                "product__category",
                "branch_supermarket__parent_supermarket",
            )
            .order_by("-similarity_name")
        )


class BranchSupermarketListView(generics.ListAPIView):
    """
    View responsible for returning supermarkets to the frontend.
    Lists all active markets, ordered by distance from the user.
    An optional radius (radiusInKm) can restrict results to a configurable
    distance; when omitted, no distance limit is applied.

    Query params:
      - latitude, longitude (used for distance calculation)
      - address (optional search term, enables fuzzy matching via pg_trgm)
      - city (optional accent/case-insensitive city filter)
      - radiusInKm (optional distance limit, e.g. "30")
    """

    serializer_class = BranchSupermarketSerializer
    pagination_class = BranchSupermarketPagination
    SIMILARITY_THRESHOLD = 0.25

    def get_queryset(self):
        user_latitude = self.request.query_params.get("latitude")
        user_longitude = self.request.query_params.get("longitude")
        city_filter = self.request.query_params.get("city")
        address_search = self.request.query_params.get("address")
        radius_override = self.request.query_params.get("radiusInKm")

        queryset = (
            BranchSupermarket.objects.select_related(
                "parent_supermarket",
            )
            .filter(product_offers__offer__expiration_date__gte=timezone.now().date())
            .distinct()
        )

        if city_filter:
            queryset = queryset.filter(city__unaccent__iexact=city_filter)

        # Fuzzy matching on the market name/address (pg_trgm). Small typos
        # ("conper" -> "Comper") and accent variations ("pao" -> "Pão") are
        # tolerated, unlike the legacy strict "icontains" substring filter.
        normalized_address = normalize_search_query(address_search)
        if normalized_address:
            queryset = queryset.annotate(
                similarity_name=TrigramSimilarity(
                    Unaccent("parent_supermarket__name"), normalized_address
                ),
                similarity_address=TrigramSimilarity(
                    Unaccent("address"), normalized_address
                ),
                relevance=Greatest(
                    F("similarity_name"), F("similarity_address")
                ),
            ).filter(
                Q(similarity_name__gt=self.SIMILARITY_THRESHOLD)
                | Q(similarity_address__gt=self.SIMILARITY_THRESHOLD)
                | Q(parent_supermarket__name__unaccent__icontains=normalized_address)
                | Q(address__unaccent__icontains=normalized_address)
            )

        try:
            user_latitude = float(user_latitude)
            user_longitude = float(user_longitude)
        except (TypeError, ValueError):
            user_location = None
        else:
            if -90 <= user_latitude <= 90 and -180 <= user_longitude <= 180:
                user_location = Point(user_longitude, user_latitude, srid=4326)
            else:
                user_location = None

        if user_location is None:
            if normalized_address:
                return queryset.order_by("-relevance")
            return queryset.order_by("parent_supermarket__name")

        results = queryset.annotate(distance=Distance("coordinates", user_location))

        # Optional configurable radius. When omitted, no distance limit is applied.
        if radius_override:
            radius_meters = float(radius_override) * 1000
            results = results.filter(
                coordinates__dwithin=(user_location, radius_meters)
            )

        if normalized_address:
            return results.order_by("-relevance", "distance")

        return results.order_by("distance")


class BranchCityListView(APIView):
    """
    View responsible for returning the distinct cities of supermarkets
    with active (non-expired) offers, ordered alphabetically.

    Query params:
      - none required
    """

    def get(self, request):
        active_cities = (
            BranchSupermarket.objects.filter(
                product_offers__offer__expiration_date__gte=timezone.now().date()
            )
            .values_list("city", flat=True)
            .distinct()
            .order_by("city")
        )
        return Response(list(active_cities))


class BranchProductOfferListView(generics.ListAPIView):
    serializer_class = BranchProductOfferSerializer
    pagination_class = OffersPagination

    def get_queryset(self):
        user_latitude = self.request.query_params.get("latitude")
        user_longitude = self.request.query_params.get("longitude")
        market_id = self.request.query_params.get("marketId")

        queryset = BranchProductOffer.objects.select_related(
            "product", "product__category", "branch_supermarket__parent_supermarket"
        )

        if market_id:
            return queryset.filter(branch_supermarket__id=market_id).order_by(
                "product__category__priority"
            )

        try:
            user_location = Point(float(user_longitude), float(user_latitude), srid=4326)
        except (ValueError, TypeError):
            return queryset.order_by("product__category__priority")

        MAXIMUM_RADIUS_METERS = 5000
        results = (
            queryset.filter(
                branch_supermarket__coordinates__dwithin=(user_location, MAXIMUM_RADIUS_METERS)
            )
            .annotate(distance=Distance("branch_supermarket__coordinates", user_location))
            .order_by("product__category__priority", "distance")
        )

        return results
