from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramSimilarity
from django.db import connection
from django.db.models import Case, F, IntegerField, Q, Value, When
from django.db.models.functions import Greatest
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
      - query: the (already normalized) search term typed by the user.
    """

    SIMILARITY_THRESHOLD = 0.25

    @staticmethod
    def _relevance_case(lookup: str, term: str) -> Case:
        """
        Builds a `Case`/`When` expression that scores how directly the search
        term matched each product: a name hit is more relevant than a brand hit,
        which in turn beats a category hit; rows matched only by fuzzy trigram
        similarity score the lowest. The same expression works on PostgreSQL
        ('__unaccent__icontains') and SQLite ('__icontains'), keeping the ordering
        contract identical across test CI and production.
        """

        return Case(
            When(**{f"product__name{lookup}": term}, then=Value(4)),
            When(**{f"product__brand{lookup}": term}, then=Value(3)),
            When(**{f"product__category__name{lookup}": term}, then=Value(2)),
            default=Value(1),
            output_field=IntegerField(),
        )

    def get(self, request):
        query = normalize_search_query(request.GET.get("query", "").strip())

        if not query:
            return Response({"offers": []})

        offers = BranchProductOffer.objects.valid().select_related(
            "product",
            "product__category",
            "branch_supermarket__parent_supermarket",
        )

        if connection.vendor == "postgresql":
            # PostgreSQL: accent-insensitive lookup plus trigram similarity on
            # name and brand (the query is de-accented by normalize_search_query,
            # so Unaccent is applied to the columns, consistent with
            # BranchProductOfferListView). Relevance is derived from which field
            # matched the term (name > brand > category > fuzzy), with the
            # trigram score used as a tie-breaker so the closest matches rank first.
            offers = offers.annotate(
                similarity_name=TrigramSimilarity(Unaccent("product__name"), query),
                similarity_brand=TrigramSimilarity(Unaccent("product__brand"), query),
            ).filter(
                Q(product__name__unaccent__icontains=query)
                | Q(product__brand__unaccent__icontains=query)
                | Q(product__category__name__unaccent__icontains=query)
                | Q(similarity_name__gt=self.SIMILARITY_THRESHOLD)
                | Q(similarity_brand__gt=self.SIMILARITY_THRESHOLD)
            )
            ordering = ["-relevance", "-similarity_name", "-similarity_brand"]
            relevance_lookup = "__unaccent__icontains"
        else:
            # SQLite (tests/CI): fallback without unaccent/pg_trgm. Relevance is
            # derived from which field matched first (name > brand > category).
            offers = offers.filter(
                Q(product__name__icontains=query)
                | Q(product__brand__icontains=query)
                | Q(product__category__name__icontains=query)
            )
            ordering = ["-relevance"]
            relevance_lookup = "__icontains"

        offers = offers.annotate(relevance=self._relevance_case(relevance_lookup, query)).order_by(
            *ordering
        )

        offers = offers[:5]

        return Response({"offers": BranchProductOfferSerializer(offers, many=True).data})


class BranchSupermarketListView(generics.ListAPIView):
    """
    View responsible for returning supermarkets to the frontend.
    Lists all active markets, ordered by distance from the user.
    An optional radius (radiusInKm) can restrict results to a configurable
    distance; when omitted, a default limit of 50 km is applied.

    Query params:
      - latitude, longitude (used for distance calculation)
      - address (optional search term, enables fuzzy matching via pg_trgm)
      - city (optional accent/case-insensitive city filter)
      - radiusInKm (optional distance limit, e.g. "30"; defaults to "50")
    """

    serializer_class = BranchSupermarketSerializer
    pagination_class = BranchSupermarketPagination
    SIMILARITY_THRESHOLD = 0.25

    def get_queryset(self):
        user_latitude = self.request.query_params.get("latitude")
        user_longitude = self.request.query_params.get("longitude")
        city_filter = self.request.query_params.get("city")
        address_search = self.request.query_params.get("address")
        radius_override = self.request.query_params.get("radiusInKm") or "50"

        queryset = (
            BranchSupermarket.objects.filter(product_offers__in=BranchProductOffer.objects.valid())
            .select_related(
                "parent_supermarket",
            )
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
                similarity_address=TrigramSimilarity(Unaccent("address"), normalized_address),
                relevance=Greatest(F("similarity_name"), F("similarity_address")),
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
            results = results.filter(coordinates__dwithin=(user_location, radius_meters))

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
            BranchSupermarket.objects.filter(product_offers__in=BranchProductOffer.objects.valid())
            .values_list("city", flat=True)
            .distinct()
            .order_by("city")
        )
        return Response(list(active_cities))


class BranchProductOfferListView(generics.ListAPIView):
    serializer_class = BranchProductOfferSerializer
    pagination_class = OffersPagination
    SIMILARITY_THRESHOLD = 0.5

    def get_queryset(self):
        user_latitude = self.request.query_params.get("latitude")
        user_longitude = self.request.query_params.get("longitude")
        market_id = self.request.query_params.get("marketId")
        search = self.request.query_params.get("search") or self.request.query_params.get("query")

        queryset = BranchProductOffer.objects.valid().select_related(
            "product", "product__category", "branch_supermarket__parent_supermarket"
        )

        has_search = False
        if search:
            normalized_search = normalize_search_query(search)
            has_search = True
            if connection.vendor == "postgresql":
                # PostgreSQL: accent-insensitive lookup plus trigram similarity so
                # searches without accents ('feijao' -> 'Feijão') and small typos
                # ('fijao' -> 'Feijão') still match, using the enabled pg_trgm and
                # unaccent extensions (migration 0004) and the GIN trgm indexes.
                # Trigram similarity is only applied to name and brand, with a high
                # threshold (0.5) so only close matches ('fijao' ~ 0.57) enter and
                # weak category-like false positives are discarded; exact category
                # searches are already covered by the icontains lookup.
                queryset = queryset.annotate(
                    similarity_name=TrigramSimilarity(Unaccent("product__name"), normalized_search),
                    similarity_brand=TrigramSimilarity(
                        Unaccent("product__brand"), normalized_search
                    ),
                ).filter(
                    Q(product__name__unaccent__icontains=normalized_search)
                    | Q(product__brand__unaccent__icontains=normalized_search)
                    | Q(product__category__name__unaccent__icontains=normalized_search)
                    | Q(similarity_name__gte=self.SIMILARITY_THRESHOLD)
                    | Q(similarity_brand__gte=self.SIMILARITY_THRESHOLD)
                )
                queryset = queryset.annotate(
                    relevance=Case(
                        When(product__name__unaccent__icontains=normalized_search, then=Value(4)),
                        When(product__brand__unaccent__icontains=normalized_search, then=Value(3)),
                        When(
                            product__category__name__unaccent__icontains=normalized_search,
                            then=Value(2),
                        ),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
            else:
                # SQLite (tests/CI): safe fallback without unaccent/pg_trgm.
                # The raw (unnormalized) term is matched as well so accented
                # data ('Feijão') can still be found in this test-only backend.
                queryset = queryset.filter(
                    Q(product__name__icontains=normalized_search)
                    | Q(product__name__icontains=search)
                    | Q(product__brand__icontains=normalized_search)
                    | Q(product__brand__icontains=search)
                    | Q(product__category__name__icontains=normalized_search)
                    | Q(product__category__name__icontains=search)
                ).annotate(
                    relevance=Case(
                        When(product__name__icontains=normalized_search, then=Value(4)),
                        When(product__brand__icontains=normalized_search, then=Value(3)),
                        When(product__category__name__icontains=normalized_search, then=Value(2)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )

        if market_id:
            queryset = queryset.filter(branch_supermarket__id=market_id)
            if has_search:
                return queryset.order_by("-relevance", "product__category__priority")
            return queryset.order_by("product__category__priority")

        try:
            user_location = Point(float(user_longitude), float(user_latitude), srid=4326)
        except (ValueError, TypeError):
            user_location = None

        if has_search:
            # Global keyword search: distance is only calculated and used for
            # ordering (relevance first, then proximity), never to exclude
            # offers regardless of how far the branch is registered.
            if user_location is not None:
                results = queryset.annotate(
                    distance=Distance("branch_supermarket__coordinates", user_location)
                )
                return results.order_by("-relevance", "distance", "price")
            return queryset.order_by("-relevance", "price")

        # Home feed without a search term: restrict to nearby branches.
        if user_location is None:
            return queryset.order_by("product__category__priority")

        MAXIMUM_RADIUS_METERS = 5000
        results = queryset.filter(
            branch_supermarket__coordinates__dwithin=(user_location, MAXIMUM_RADIUS_METERS)
        ).annotate(distance=Distance("branch_supermarket__coordinates", user_location))
        return results.order_by("distance", "price")
