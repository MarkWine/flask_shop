from dataclasses import dataclass
from decimal import Decimal

from flask import jsonify, session
from sqlalchemy.exc import SQLAlchemyError

from shop import db
from .shipping import (
    ShippingAddress,
    DestinationAddress,
    ORIGIN_ADDRESS,
    SHIPENGINE_GET_RATES,
)
from ..orders.models import OrderItem, Order

SHIPPING_OPTIONS = {
    "Standard": {
        "services": {"FEDEX_GROUND", "USPS_FIRST_CLASS", "USPS_PRIORITY"},
        "handling": 0,
    },
    "Express": {"services": {"USPS_FIRST_CLASS"}, "handling": 2.5},
}


class CartSession(db.Model):
    __tablename__ = "shopping_cart"

    id = db.Column(db.Integer, primary_key=True)
    postal_code = db.Column(db.String)
    name = db.Column(db.String)
    company_name = db.Column(db.String)
    address_line1 = db.Column(db.String)
    address_line2 = db.Column(db.String)
    city = db.Column(db.String)
    state = db.Column(db.String)
    country = db.Column(db.String)
    shipping_selected = db.Column(db.Integer)

    @property
    def shipping_address(self):
        shipping_address = DestinationAddress(
            postal_code=self.ship_postal_code,
            name=self.ship_name,
            company_name=self.ship_company,
            address_line1=self.ship_address,
            address_line2=self.ship_address2,
            city=self.ship_city,
            state=self.ship_state,
            country=self.ship_country,
            origin_address=ORIGIN_ADDRESS or ShippingAddress("98101"),
        )
        return shipping_address

    def get_shipping_rates(self):
        all_carriers = set.union(
            *[option["services"] for option in SHIPPING_OPTIONS.values()]
        )
        rates = {}
        if SHIPENGINE_GET_RATES:
            rates.update(self.shipping_address.get_shipengine())
        if all_carriers & {"USPS_FIRST_CLASS", "USPS_PRIORITY"}:
            rates.update(self.shipping_address.get_usps_domestic())
        if all_carriers & {"FEDEX_GROUND"}:
            rates.update(self.shipping_address.get_fedex_rates())
        for option in SHIPPING_OPTIONS:
            session["option"] = min(rates[SHIPPING_OPTIONS[option]])
        pass

    @property
    def shipping_normal(self):
        return Decimal("3.02")

    @property
    def shipping_expedited(self):
        return Decimal("4.19")

    @property
    def shipping_cost(self):
        return self.shipping_expedited if self.selected == 1 else self.shipping_normal

    @property
    def subtotal(self):
        return sum([item.subtotal for item in self.cart_items])

    @property
    def total(self):
        return self.subtotal + self.shipping_cost

    @property
    def json(self):
        json = {
            "shipping_normal": str(self.shipping_normal),
            "shipping_expedited": str(self.shipping_expedited),
            "shipping_selected": str(self.shipping_selected),
            "shipping_cost": str(self.shipping_cost),
            "subtotal": str(self.subtotal),
            "total": str(self.total),
        }
        return jsonify(json)

    def convert_cart(self, payment, address=None):
        """
        Turn a cart into an order based on payment information
        :param payment: Payment
        :param address: ShippingAddress
        :return:
        """
        if not address:
            address = self.shipping_address
        order = Order(payment_id=payment.id, payment_type=payment.type, address=address)
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

    @property
    def unit_price(self):
        return self.product.price

    @property
    def subtotal(self):
        return self.unit_price * Decimal(self.quantity)

    product = db.relationship("Product")
    cart = db.relationship("CartSession", backref=db.backref("cart_items"))


class Payment:
    def __init__(self, id, payment_type, payment_total, address=None):
        self.id = id
        self.payment_type = payment_type


@dataclass
class OrderPayment:
    id: str
    payment_type: str
    payment_total: str
    buyer_first: str
    buyer_last: str
    address: ShippingAddress
