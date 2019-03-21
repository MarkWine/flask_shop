from flask import Blueprint, render_template, request
from flask_security import login_required, roles_accepted

from shop import db
from ..orders.models import Order, OrderItem

admin_blueprint: Blueprint = Blueprint(
    name="admin", import_name=__name__, template_folder="templates"
)


@login_required
@roles_accepted("admin")
@admin_blueprint.route("/admin")
def admin_view():
    return render_template("admin_index.html")


@login_required
@roles_accepted("admin")
@admin_blueprint.route("/admin/orders")
def orders_view():
    if request.args.get("id"):
        order = db.session.query(Order).get(request.args.get("id"))
        return render_template("order.html", order=order)
    return render_template("orders.html")
