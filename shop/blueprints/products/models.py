from dataclasses import dataclass

from shop import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    inventory_quantity = db.Column(db.Integer)
    price = db.Column(db.Numeric(8, 2))
    weight = db.Column(db.Numeric(8, 2))


class Variant(db.Model):
    __tablename__ = "product_variants"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    name = db.Column(db.String)
    inventory_quantity = db.Column(db.Integer)
    price = db.Column(db.Numeric(8, 2))
    weight = db.Column(db.Numeric)

    product = db.relationship("Product", backref=db.backref("variants"))


@dataclass
class ItemList:
    """
    List of potentially sorted items
    """
    category_id: int
    filter_options: list
    sort_options: list

    @property
    def item_dict(self):
        """
        get items based on input
        :return: products
        """
        products = Product.query.filter(self.category_id in Product.categories)
        return products
