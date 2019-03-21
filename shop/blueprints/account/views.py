from flask import Blueprint, request, render_template

account_blueprint: Blueprint = Blueprint("account", import_name=__name__)


@account_blueprint.route("/account/")
def account_view():
    render_template("account.html")


@account_blueprint.route("/wishlist/")
def wishlist():
    if request.args:
        pass
    render_template("wishlist.html")


@account_blueprint.route("/orders/")
def account_orders():
    render_template("orders.html")
