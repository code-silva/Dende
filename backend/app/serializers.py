from rest_framework import serializers

from .models import BranchProductOffer, BranchSupermarket

"""
The serializer transforms what would be a field with an ID and looks up in the table
where the ID came from to return the value we passed and ultimately delivers a JSON.
"""


class BranchSupermarketSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for returning 'BranchSupermarket' entity information
    in a readable format for the mobile frontend (JSON).

    Returns:

    {
        "id": Unique identifier of the store,
        "name": Store name,
        "state": State where the store is located,
        "city": City where the store is located,
        "distanceInKilometers": Straight-line distance to the user
    }
    """

    class Meta:
        model = BranchSupermarket
        fields = ["id", "name", "state", "city", "address", "distanceInKilometers"]

    name = serializers.CharField(source="parent_supermarket.name", read_only=True)
    state = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    address = serializers.CharField(read_only=True)

    distanceInKilometers = serializers.SerializerMethodField()

    def get_distanceInKilometers(self, obj):
        # 'distance' is the virtual field defined by 'annotate'
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None


class BranchProductOfferSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for returning 'BranchProductOffer' entity information
    in a structured and readable format for the mobile frontend (JSON).
    This serializer aggregates data from multiple related entities: Product,
    Category, and Supermarket.

    Returns:

    {
        "id": Unique identifier of the offer,
        "productName": Name of the product associated with the offer,
        "brand": Product brand,
        "price": Current price of the product at the store,
        "image": Product image URL,
        "measurementUnit": Product measurement unit (e.g., kg, un, L),
        "measurement": Quantity corresponding to the measurement unit,
        "marketName": Name of the store where the offer is available,
        "categoryName": Product category,
        "distanceInKilometers": Straight-line distance to the user (when available)
    }
    """

    productName = serializers.CharField(source="product.name", read_only=True)
    brand = serializers.CharField(source="product.brand", read_only=True)
    image = serializers.ImageField(source="product.image", read_only=True)

    measurementUnit = serializers.CharField(
        source="product.get_measurement_unit_display", read_only=True
    )

    measurement = serializers.DecimalField(
        source="product.measurement", max_digits=10, decimal_places=2, read_only=True
    )

    marketName = serializers.CharField(
        source="branch_supermarket.parent_supermarket.name", read_only=True
    )

    categoryName = serializers.CharField(source="product.category.name", read_only=True)

    distanceInKilometers = serializers.SerializerMethodField()

    class Meta:
        model = BranchProductOffer
        fields = [
            "id",
            "productName",
            "brand",
            "price",
            "image",
            "measurementUnit",
            "measurement",
            "marketName",
            "categoryName",
            "distanceInKilometers",
        ]

    def get_distanceInKilometers(self, obj):
        if hasattr(obj, "distance") and obj.distance is not None:
            return round(obj.distance.km, 2)
        return None
