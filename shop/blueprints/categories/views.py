from flask import Blueprint, render_template, jsonify, request

from .models import Category

category_blueprint: Blueprint = Blueprint(name="category", import_name=__name__, template_folder="templates")


@category_blueprint.route("/category/<name>")
def category_page(name):
    category = Category.query.filter(Category.name == name).first_or_404()
    return render_template("category.html", category=category)


@category_blueprint.route("/api/items")
def item_api():
    filter_name = request.json.get("filter")
    response = {"filter": filter_name}
    return jsonify(response)
