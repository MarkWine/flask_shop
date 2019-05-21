from dataclasses import dataclass

from ..products.models import Product
from shop import db


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    products = db.relationship("Product",
                               secondary="product_categories",
                               backref=db.backref("categories"))


class ProductCategory(db.Model):
    __tablename__ = "product_categories"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    product = db.relationship("Product", backref=db.backref("product_categories"))


class Filter(db.Model):
    """
    e.g. style, color
    """
    __tablename__ = "filters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class FilterOptions(db.Model):
    """
    e.g. large, red
    """
    __tablename__ = "filter_options"
    id = db.Column(db.Integer, primary_key=True)
    filter_id = db.Column(db.Integer, db.ForeignKey("filters.id"))
    name = db.Column(db.String)


class FilterCategories(db.Model):
    """
    Which filters should show up for different category selections
    """
    id = db.Column(db.Integer, primary_key=True)
    filter_id = db.Column(db.Integer, db.ForeignKey("filters.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))


class FilterProduct(db.Model):
    __tablename__ = "product_filters"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    filter_option_id = db.Column(db.Integer, db.ForeignKey("filter_options.id"))


