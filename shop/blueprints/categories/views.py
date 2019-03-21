from flask import Blueprint

category_blueprint: Blueprint = Blueprint(name="category", import_name=__name__)


@category_blueprint.route("/category/<name>")
def category():
    return True
