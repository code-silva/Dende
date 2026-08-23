import pytest
from django.db import IntegrityError
from model_bakery import baker

from app.models import BranchSupermarket, Category, Offer, ParentSupermarket


@pytest.mark.django_db
class TestCategory:
    """
    Class destined to the elaboration of tests of 'Category' model.
    """

    def test_name_uniqueness(self):
        """
        Tests if the 'unique' constraint is applied to the 'name' attribute.
        It should return an error if you try to create a category with the same name
        as an existing one.
        """

        baker.make(Category, name="arroz")
        with pytest.raises(IntegrityError):
            baker.make(Category, name="arroz")

    def test_priority_uniqueness(self):
        """
        Tests if the 'unique' constraint is applied to the 'priority' attribute.
        It should return an error if you try to create a category with the same priority
        as an existing one.
        """

        baker.make(Category, priority=1)
        with pytest.raises(IntegrityError):
            baker.make(Category, priority=1)

    def test_string_casing_normalization(self):
        """Tests if the Category name is correctly normalized upon save."""
        category = baker.make(Category, name=" PRODUTOS  de   limpeza ")
        assert category.name == "Produtos de Limpeza"


@pytest.mark.django_db
class TestProduct:
    """
    Class destined to the elaboration of tests of 'Product' model.
    """

    def test_string_casing_normalization(self):
        """Tests if the Product name and brand are correctly normalized upon save."""
        from app.models import Product

        product = baker.make(Product, name="arroz branco tipo 1", brand="TIO JOÃO")
        assert product.name == "Arroz Branco Tipo 1"
        assert product.brand == "Tio João"

    @pytest.mark.skip(reason="SQLite doesn't support composite unique constraint.")
    def test_product_uniqueness(self):
        """Tests if the composite unique constraint works on Product."""
        from app.models import Category, Product

        category = baker.make(Category)
        baker.make(
            Product,
            name="arroz",
            category=category,
            brand="tio joão",
            measurement=1.0,
            measurement_unit="KG",
        )
        with pytest.raises(IntegrityError):
            baker.make(
                Product,
                name="arroz",
                category=category,
                brand="tio joão",
                measurement=1.0,
                measurement_unit="KG",
            )

    def test_create_different_products(self):
        """Tests happy path: creating products that vary slightly in their composite fields."""
        from app.models import Category, Product

        category = baker.make(Category)
        baker.make(
            Product,
            name="arroz",
            category=category,
            brand="tio joão",
            measurement=1.0,
            measurement_unit="KG",
        )
        baker.make(
            Product,
            name="arroz",
            category=category,
            brand="camil",
            measurement=1.0,
            measurement_unit="KG",
        )
        assert Product.objects.count() == 2


@pytest.mark.django_db
class TestParentSupermarket:
    """
    Class destined to the elaboration of tests of 'ParentSupermarket' model.
    """

    def test_name_uniqueness(self):
        """
        Tests if the 'unique' constraint is applied to the 'name' attribute.
        It should return an error if you try to create a parent_supermarket with
        the same name as an existing one.
        """

        baker.make(ParentSupermarket, name="Dia a Dia")
        with pytest.raises(IntegrityError):
            baker.make(ParentSupermarket, name="Dia a Dia")

    def test_string_casing_normalization(self):
        """Tests if the ParentSupermarket name is correctly normalized upon save."""
        market1 = baker.make(ParentSupermarket, name="ULTRABOX")
        assert market1.name == "Ultrabox"

        market2 = baker.make(ParentSupermarket, name="  pão  de   açúcar  ")
        assert market2.name == "Pão de Açúcar"


@pytest.mark.django_db
class TestBranchSupermarket:
    """
    Class destined to the elaboration of tests of 'BranchSupermarket' model.
    """

    @pytest.mark.skip(reason="SQLite doesn't support composite unique constraint.")
    def test_coordinates_and_parent_supermarket_uniqueness(self):
        """
        Tests if the 'unique' constraint is applied to the 'coordinates' and 'parent_supermarket'
        attribute. It should return an error if you try to create a branch_supermarket with
        the same coordiantes and parent_supermarket as an existing one.
        """

        parent_supermarket = baker.make(ParentSupermarket)

        # The coordiantes, by default, is Point(0, 0) thanks to the fixture
        # in the conftest.py file. So there's no need to pass the coordinates argument.
        baker.make(BranchSupermarket, parent_supermarket=parent_supermarket)
        with pytest.raises(IntegrityError):
            baker.make(BranchSupermarket, parent_supermarket=parent_supermarket)


@pytest.mark.django_db
class TestOffer:
    """
    Class destined to the elaboration of tests of 'Offer' model.
    """

    def test_url_uniqueness(self):
        """
        Tests if the 'unique' constraint is applied to the 'url' attribute.
        It should return an error if you try to create an offer with
        the same url as an existing one.
        """

        baker.make(Offer, url="https://www.test.com")
        with pytest.raises(IntegrityError):
            baker.make(Offer, url="https://www.test.com")


@pytest.mark.django_db
class TestBranchProductOffer:
    """
    Class destined to the elaboration of tests of 'BranchProductOffer' model.
    """

    @pytest.mark.skip(reason="SQLite doesn't support composite unique constraint.")
    def test_branch_product_offer_uniqueness(self):
        from app.models import BranchProductOffer, BranchSupermarket, Offer, Product

        product = baker.make(Product)
        branch = baker.make(BranchSupermarket)
        offer = baker.make(Offer)
        baker.make(
            BranchProductOffer, product=product, branch_supermarket=branch, offer=offer, price=10.0
        )
        with pytest.raises(IntegrityError):
            baker.make(
                BranchProductOffer,
                product=product,
                branch_supermarket=branch,
                offer=offer,
                price=15.0,
            )

    def test_create_different_branch_product_offers(self):
        from app.models import BranchProductOffer, BranchSupermarket, Offer, Product

        product1 = baker.make(Product)
        product2 = baker.make(Product)
        branch = baker.make(BranchSupermarket)
        offer = baker.make(Offer)
        baker.make(
            BranchProductOffer, product=product1, branch_supermarket=branch, offer=offer, price=10.0
        )
        baker.make(
            BranchProductOffer, product=product2, branch_supermarket=branch, offer=offer, price=15.0
        )
        assert BranchProductOffer.objects.count() == 2
