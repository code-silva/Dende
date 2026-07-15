from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
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
from .utils import remove_accents


class HybridSearchView(APIView):
    """
    View responsible for performing a unified search across both product offers and
    supermarkets. It uses trigram similarity and text filtering to find relevant
    results based on names, brands, or categories.
    """

    def get(self, request):
        query = remove_accents(request.GET.get("query", "").strip())
        SIMILARITY_THRESHOLD = 0.25

        if not query:
            return Response({"offers": []})

        offers = (
            BranchProductOffer.objects.annotate(
                similarity_name=TrigramSimilarity("product__name", query),
                similarity_brand=TrigramSimilarity("product__brand", query),
            )
            .filter(
                Q(product__name__unaccent__icontains=query)
                | Q(product__brand__unaccent__icontains=query)
                | Q(product__category__name__unaccent__icontains=query)
                | Q(similarity_name__gt=SIMILARITY_THRESHOLD)
                | Q(similarity_brand__gt=SIMILARITY_THRESHOLD)
            )
            .select_related(
                "product",
                "product__category",
                "branch_supermarket__parent_supermarket",
            )
            .order_by("-similarity_name")
        )

        return Response({"offers": BranchProductOfferSerializer(offers, many=True).data})


class BranchSupermarketListView(generics.ListAPIView):
    """
    View responsible for returning supermarkets to the frontend, within a radius of up to 5km
    from the user. This view ALWAYS returns a list of objects.
    """

    serializer_class = BranchSupermarketSerializer
    pagination_class = BranchSupermarketPagination

    def get_queryset(self):
        user_latitude = self.request.query_params.get("latitude")
        user_longitude = self.request.query_params.get("longitude")

        queryset = (
            BranchSupermarket.objects.select_related(
                "parent_supermarket",
            )
            .filter(product_offers__offer__expiration_date__gte=timezone.now().date())
            .distinct()
        )

        try:
            user_location = Point(float(user_longitude), float(user_latitude), srid=4326)
        except (ValueError, TypeError):
            return queryset.order_by("parent_supermarket__name")

        MAXIMUM_RADIUS_METERS = 5000
        results = (
            queryset.filter(coordinates__dwithin=(user_location, MAXIMUM_RADIUS_METERS))
            .annotate(distance=Distance("coordinates", user_location))
            .order_by("distance")
        )

        return results


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
