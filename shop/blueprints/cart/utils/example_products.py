from shop.blueprints.products.models import Product
from shop.blueprints.cart.models import CartItem, CartSession
from shop import db


def make_example_cart(cart_id):
    hat = Product(name="Hat", inventory_quantity=4, price="3.24", weight=7)
    db.session.add(hat)

    pen = Product(name="Pen", inventory_quantity=100, price=".99", weight=1)
    db.session.add(pen)
    db.session.commit()
    cart_hat = CartItem(cart_id=cart_id, product_id=hat.id, quantity=1)
    db.session.add(cart_hat)

    cart_pens = CartItem(cart_id=cart_id, product_id=pen.id, quantity=3)
    db.session.add(cart_pens)

    db.session.commit()
