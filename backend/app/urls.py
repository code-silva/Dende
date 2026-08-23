from django.urls import path

from .views import (
    BranchCityListView,
    BranchProductOfferListView,
    BranchSupermarketListView,
    HybridSearchView,
)

urlpatterns = [
    path("search/", HybridSearchView.as_view(), name="search"),
    path("nearby-markets/", BranchSupermarketListView.as_view(), name="nearby_markets"),
    path("cities/", BranchCityListView.as_view(), name="cities_list"),
    path("products/offers/", BranchProductOfferListView.as_view(), name="offers_list"),
]
