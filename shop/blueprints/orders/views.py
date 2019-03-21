from flask import Blueprint
from flask_security import roles_accepted, login_required

from .models import Order, OrderItem

order_blueprint: Blueprint = Blueprint(name="order", import_name=__name__)


@login_required
@roles_accepted("admin")
@order_blueprint.route("/admin/orders")
def orders_page():
    return
