import pytest
from shop.blueprints.products.models import Product


@pytest.fixture()
def product_test():
    product = Product()
    return product
