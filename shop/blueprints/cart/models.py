from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json

from flask import jsonify, session, current_app
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
        "handling": Decimal("0.00"),
        "default": Decimal("2.50"),
    },
    "Express": {
        "services": {"USPS_PRIORITY"},
        "handling": Decimal("2.50"),
        "default": Decimal("5.00"),
    },
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
    shipping_selected = db.Column(db.String)
    cart_created = db.Column(db.DateTime)

    def __init__(self):
        self.shipping_selected = "Standard"
        self.cart_created = datetime.now()

    @property
    def shipping_address(self):
        shipping_address = DestinationAddress(
            postal_code=self.postal_code,
            name=self.name,
            company_name=self.company_name,
            address_line1=self.address_line1,
            address_line2=self.address_line2,
            city=self.city,
            state=self.state,
            country=self.country,
            origin_address=ORIGIN_ADDRESS or ShippingAddress("98101"),
        )
        return shipping_address

    def get_shipping_rates(self):
        all_carriers = set.union(
            *[option["services"] for option in SHIPPING_OPTIONS.values()]
        )
        session["rates_updated"] = str(datetime.now())
        rates = {}
        if SHIPENGINE_GET_RATES:
            rates.update(self.shipping_address.get_shipengine(weight=self.weight))
        if all_carriers & {"USPS_FIRST_CLASS", "USPS_PRIORITY"}:
            rates.update(self.shipping_address.get_usps_domestic(weight=self.weight))
            current_app.logger.info("USPS Updated")
        if all_carriers & {"FEDEX_GROUND"}:
            rates.update(self.shipping_address.get_fedex_rates(weight=self.weight))
        current_app.logger.info(str(rates))
        for option in SHIPPING_OPTIONS:
            try:
                best_rate = min(
                    {
                        service: rates[service]
                        for service in SHIPPING_OPTIONS[option]["services"]
                        if rates[service] is not None
                    }.values()
                )
                session[option] = best_rate
                current_app.logger.info(f"{rates}: {option}: {best_rate}")
            except ValueError:
                return None
        return rates

    @property
    def weight(self):
        return sum(item.product.weight * item.quantity for item in self.cart_items)

    @property
    def shipping_rates(self):
        current_app.logger.info(f"weight: {self.weight}")
        if not session.get("rates_updated"):
            self.get_shipping_rates()
        try:
            current_app.logger.info(f"session rates?: {str(session)}")
            rates = {
                k: Decimal(session[k]) + v["handling"]
                for k, v in SHIPPING_OPTIONS.items()
            }
        except KeyError:
            current_app.logger.info(f"no session rates: {str(session)}")
            rates = {
                k: v["default"] + v["handling"] for k, v in SHIPPING_OPTIONS.items()
            }
        current_app.logger.info(f"rates: {str(rates)}")
        return rates

    @property
    def shipping_cost(self):
        return self.shipping_rates[self.shipping_selected or "Standard"]

    @property
    def subtotal(self):
        return sum([item.subtotal for item in self.cart_items])

    @property
    def total(self):
        return self.subtotal + self.shipping_cost

    @property
    def json(self):
        cart_json = {
            "shipping_selected": str(self.shipping_selected),
            "shipping_cost": str(self.shipping_cost),
            "subtotal": str(self.subtotal),
            "total": str(self.total),
        }
        for option in SHIPPING_OPTIONS:
            cart_json[option] = str(self.shipping_rates[option])
        return jsonify(cart_json)

    def convert_cart(self, payment, address=None):
        """
        Turn a cart into an order based on payment information
        :param payment: OrderPayment
        :param address: ShippingAddress
        :return:
        """
        if not address:
            address = self.shipping_address
        order = Order(
            payment_id=payment.id,
            payment_type=payment.payment_type,
            cart_id=self.id,
            payment_total=payment.payment_total,
            shipping_cost=self.shipping_cost,
            shipping_service=self.shipping_selected,
            buyer_first_name=payment.buyer_first,
            buyer_last_name=payment.buyer_last,
            address=address,
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
        return order

    def convert_amazon_order(self, order_response):
        try:
            confirm_result = json.loads(order_response.to_json())[
                "GetOrderReferenceDetailsResponse"
            ]["GetOrderReferenceDetailsResult"]["OrderReferenceDetails"]
        except KeyError:
            return "Order Not Confirmed by Amazon"
        address = confirm_result["Destination"]["PhysicalDestination"]
        shipping_address = ShippingAddress(
            postal_code=address["PostalCode"],
            name=confirm_result["Buyer"]["Name"],
            address_line1=address["AddressLine1"],
            address_line2=address.get("AddressLine1"),
            city=address["City"],
            state=address["StateOrRegion"],
            country=address.get("CountryCode"),
        )
        payment = OrderPayment(
            id=confirm_result.get("AmazonOrderReferenceId"),
            payment_type="PayWithAmazon",
            buyer_first=confirm_result["Buyer"]["Name"],
            payment_total=confirm_result["OrderTotal"]["Amount"],
        )
        order = self.convert_cart(payment=payment, address=shipping_address)
        return order


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


@dataclass
class OrderPayment:
    id: str
    payment_type: str
    payment_total: str
    buyer_first: str = ""
    buyer_last: str = ""
