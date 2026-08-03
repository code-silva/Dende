from rest_framework.pagination import PageNumberPagination


class BranchSupermarketPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 100


class OffersPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100
