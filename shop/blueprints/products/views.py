from flask import Blueprint, render_template
from .models import Product


product_blueprint: Blueprint = Blueprint(name="product", import_name=__name__, template_folder="templates")


@product_blueprint.route("/product/<product_id>")
def product_page(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_page.html", product=product)
