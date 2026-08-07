from django.contrib.gis.db import models as gis_models
from django.db import models


class Category(models.Model):
    """Class representing the 'Category' entity in the database."""

    name = models.CharField(max_length=50, blank=False, unique=True)
    priority = models.IntegerField(null=False, blank=False, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"


class Product(models.Model):
    """Class representing the 'Product' entity in the database."""

    class MeasurementUnit(models.TextChoices):
        KG = "KG", "KG"
        G = "G", "G"
        L = "L", "L"
        ML = "ML", "ML"
        UN = "UN", "UN"

    name = models.CharField(max_length=100, blank=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.CharField(max_length=100, blank=False)
    measurement = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/")

    measurement_unit = models.CharField(
        max_length=50, choices=MeasurementUnit.choices, default=MeasurementUnit.UN
    )

    european_article_number = models.CharField(max_length=20, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return f"{self.name} {self.brand} - {self.measurement}{self.measurement_unit}"


class ParentSupermarket(models.Model):
    """Class representing the 'ParentSupermarket' entity in the database."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Supermercado Matriz"
        verbose_name_plural = "Supermercados Matrizes"

    def __str__(self):
        return f"{self.name}"


class Offer(models.Model):
    """Class representing the 'Offer' entity in the database."""

    url = models.URLField(max_length=2083, blank=False, unique=True)
    expiration_date = models.DateField()

    class Meta:
        verbose_name = "Oferta"
        verbose_name_plural = "Ofertas"

    def __str__(self):
        return f"Expires on {self.expiration_date}"


class Report(models.Model):
    """Class representing the 'Report' entity in the database."""

    class ReportReason(models.TextChoices):
        WRONG_PRICE = "WP", "Wrong Price"
        NONEXISTENT_PRODUCT = "NP", "Nonexistent Product"
        EXPIRED_OFFER = "EO", "Expired Offer"
        OTHER = "O", "Other"

    class Status(models.TextChoices):
        RESOLVED = "R", "Resolved"
        PENDING = "P", "Pending"
        GROUNDLESS = "I", "Groundless"

    reason = models.CharField(max_length=20, choices=ReportReason.choices)
    description = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    device_id = models.CharField(max_length=255)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="reports")

    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Denúncia"
        verbose_name_plural = "Denúncias"

    def __str__(self):
        return f"Report {self.get_reason_display()} - {self.get_status_display()}"


class BranchSupermarket(models.Model):
    """Class representing the 'BranchSupermarket' entity in the database."""

    class State(models.TextChoices):
        AC = "AC", "Acre"
        AL = "AL", "Alagoas"
        AP = "AP", "Amapá"
        AM = "AM", "Amazonas"
        BA = "BA", "Bahia"
        CE = "CE", "Ceará"
        DF = "DF", "Distrito Federal"
        ES = "ES", "Espírito Santo"
        GO = "GO", "Goiás"
        MA = "MA", "Maranhão"
        MT = "MT", "Mato Grosso"
        MS = "MS", "Mato Grosso do Sul"
        MG = "MG", "Minas Gerais"
        PA = "PA", "Pará"
        PB = "PB", "Paraíba"
        PR = "PR", "Paraná"
        PE = "PE", "Pernambuco"
        PI = "PI", "Piauí"
        RJ = "RJ", "Rio de Janeiro"
        RN = "RN", "Rio Grande do Norte"
        RS = "RS", "Rio Grande do Sul"
        RO = "RO", "Rondônia"
        RR = "RR", "Roraima"
        SC = "SC", "Santa Catarina"
        SP = "SP", "São Paulo"
        SE = "SE", "Sergipe"
        TO = "TO", "Tocantins"

    coordinates = gis_models.PointField(geography=True, srid=4326)
    address = models.CharField(max_length=255, blank=False, default="")
    state = models.CharField(max_length=20, choices=State.choices, default="DF")
    city = models.CharField(max_length=50, blank=False, default="")
    parent_supermarket = models.ForeignKey(
        ParentSupermarket, on_delete=models.CASCADE, related_name="branches"
    )

    class Meta:
        verbose_name = "Supemercado Filial"
        verbose_name_plural = "Supemercado Filiais"
        constraints = [
            models.UniqueConstraint(
                fields=["coordinates", "parent_supermarket"],
                name="unique_coordinates_parent_supermarket",
            )
        ]

    def __str__(self):
        return f"{self.parent_supermarket.name} - {self.city}"


class BranchProductOffer(models.Model):
    """Class representing the associative entity that performs the link
    of the ternary relationship between 'Product', 'Offer' and 'Branch Supermarket'.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="branch_offers")
    branch_supermarket = models.ForeignKey(
        BranchSupermarket, on_delete=models.CASCADE, related_name="product_offers"
    )
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="branch_product_links")
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Produto Ofertado"
        verbose_name_plural = "Produtos Ofertados"

    def __str__(self):
        return f"{self.product.name} at {self.branch_supermarket}: $ {self.price}"
