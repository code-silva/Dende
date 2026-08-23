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
