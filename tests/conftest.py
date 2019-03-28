import pytest
from shop.blueprints.products.models import Product
from shop.blueprints.cart.models import CartSession, CartItem


@pytest.fixture
def product_test():
    product_test = Product()
    return product_test


@pytest.fixture
def cart_test():
    cart_test = CartSession()
    cart_item_1 = CartItem()
    return cart_test
