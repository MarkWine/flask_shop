from dataclasses import dataclass

from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from shop import db
from .shipping import ShippingAddress
from ..orders.models import OrderItem, Order


class CartSession(db.Model):
    __tablename__ = "shopping_cart"

    id = db.Column(db.Integer, primary_key=True)
    postal_code = db.Column(db.String)
    name = db.Column(db.String)
    company_name = db.Column(db.String)
    address_line1 = db.Column(db.String)
    address2_line2 = db.Column(db.String)
    city = db.Column(db.String)
    state = db.Column(db.String)
    country = db.Column(db.String)
    shipping_selected = db.Column(db.Integer)

    @property
    def shipping_address(self):
        shipping_address = ShippingAddress(
            postal_code=self.ship_postal_code,
            name=self.ship_name,
            company_name=self.ship_company,
            address_line1=self.ship_address,
            address_line2=self.ship_address2,
            city=self.ship_city,
            state=self.ship_state,
            country=self.ship_country,
        )
        return shipping_address

    @property
    def shipping_normal(self):
        return 3

    @property
    def shipping_expedited(self):
        return 4

    @property
    def shipping_cost(self):
        return (
            self.shipping_normal
            if self.shipping_expedited == 0
            else self.shipping_expedited
        )

    @property
    def subtotal(self):
        return sum([item.subtotal for item in self.cart_items])

    @property
    def total(self):
        return self.subtotal + self.shipping_cost

    @property
    def json(self):
        json = {
            "shipping_normal": self.shipping_normal,
            "shipping_expedited": self.shipping_expedited,
            "shipping_selected": self.shipping_selected,
            "subtotal": self.subtotal,
            "total": self.total,
        }
        return jsonify(json)

    def convert_cart(self, payment):
        order = Order(
            payment_id=payment.id,
            payment_type=payment.type,
            **vars(self.shipping_address)
        )
        db.session.add(order)
        order_items = []
        for item in self.cart_items:
            order_items.append(OrderItem(item))
        db.session.bulk_save_objects(order_items)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
        return order.id


class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("shopping_cart.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product_variant = db.Column(db.Integer, db.ForeignKey("product_variants.id"))
    quantity = db.Column(db.Integer)
    item_subtotal = db.Column(db.Numeric(8, 2))

    cart = db.relationship("CartSession", backref=db.backref("cart_items"))


@dataclass
class Payment:
    id: str
    type: str
    payment_total: str
