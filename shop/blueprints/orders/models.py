from shop import db


class Order(db.Model):
    """
    This represents a completed order and connects to orders table.
    The address can be constructed either using a ShippingAddress Object
    or by directly providing the address data as keyword arguments.
    """

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("shopping_cart.id"))
    payment_id = db.Column(db.String)
    payment_type = db.Column(db.String)
    shipping_service = db.Column(db.String)
    shipping_cost = db.Column(db.Numeric(6, 2))
    payment_total = db.Column(db.Numeric(8, 2))
    buyer_first_name = db.Column(db.String)
    buyer_last_name = db.Column(db.String)
    ship_postal_code = db.Column(db.String)
    ship_name = db.Column(db.String)
    ship_company = db.Column(db.String)
    ship_address = db.Column(db.String)
    ship_address2 = db.Column(db.String)
    ship_city = db.Column(db.String)
    ship_state = db.Column(db.String)
    ship_country = db.Column(db.String)

    def __init__(self, address=None, **kwargs):
        super(Order, self).__init__(**kwargs)
        if address:
            self.ship_postal_code = address.postal_code
            self.ship_name = address.name
            self.ship_company = address.company_name
            self.ship_address = address.address_line1
            self.ship_address2 = address.address_line2
            self.ship_city = address.city
            self.ship_state = address.state
            self.ship_country = address.country


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    product_variant = db.Column(db.Integer, db.ForeignKey("product_variants.id"))
    quantity = db.Column(db.Integer)
    item_subtotal = db.Column(db.Numeric(8, 2))

    order = db.relationship("Order", backref=db.backref("order_items"))
    product = db.relationship("Product", backref=db.backref("ordered_items"))
