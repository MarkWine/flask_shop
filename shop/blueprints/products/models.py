from shop import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    inventory_quantity = db.Column(db.Integer)


class Variant(db.Model):
    __tablename__ = "product_variants"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    name = db.Column(db.String)
    inventory_quantity = db.Column(db.Integer)

    product = db.relationship("Product", backref=db.backref("variants"))
