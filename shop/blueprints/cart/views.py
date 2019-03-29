import json
import os

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
import paypalrestsdk

from shop import db
from .models import CartSession, CartItem, SHIPPING_OPTIONS
from .amazon import client, AMAZON_CLIENT_ID, MWS_ACCESS_KEY
from .paypal import create_payment, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET
from .utils.example_products import make_example_cart
from ..orders.models import Order

cart_blueprint: Blueprint = Blueprint(
    name="cart", import_name=__name__, template_folder="templates"
)


@cart_blueprint.route("/cart")
def cart_page():
    try:
        cart_session = CartSession.query.get(session["session_id"])
        if not cart_session:
            raise TypeError
    except (KeyError, TypeError):
        cart_session = CartSession()
        db.session.add(cart_session)
        db.session.commit()
        session["session_id"] = cart_session.id
    if (
        not cart_session.cart_items
        and current_app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    ):
        make_example_cart(session["session_id"])
    return render_template("cart.html", cart_session=cart_session)


@cart_blueprint.route("/checkout")
def checkout():
    return render_template("checkout.html")


@cart_blueprint.route("/thank_you")
def thank_you_page():
    order = Order.query.get(request.args.get("order_id"))
    return render_template("thank_you.html", order=order)


@cart_blueprint.route("/api/update_postal_code", methods=["POST"])
def update_postal_code():
    cart = CartSession.query.get(session["session_id"])
    cart.postal_code = request.json.get("postal_code")
    session["rates_updated"] = False
    db.session.commit()
    return cart.json


@cart_blueprint.route("/api/shipping_select", methods=["POST"])
def update_shipping_selection():
    cart = CartSession.query.get(session["session_id"])
    cart.shipping_selected = request.json.get("shipping_select")
    db.session.commit()
    return cart.json


@cart_blueprint.route("/api/init_shipping", methods=["POST"])
def initial_shipping():
    cart = CartSession.query.get(session["session_id"])
    return cart.json


@cart_blueprint.route("/api/update_quantity", methods=["POST"])
def update_quantity():
    item = CartItem.query.get(request.json.get("item_id")) or CartItem()
    item.quantity = request.json.get("quantity")
    db.session.commit()
    cart = CartSession.query.get(session["session_id"])
    session["rates_updated"] = False
    return cart.json


@cart_blueprint.route("/api/remove_item", methods=["POST"])
def remove_item():
    try:
        item = CartItem.query.get(request.json.get("item_id"))
        db.session.delete(item)
        db.session.commit()
    except KeyError:
        return {"Item already deleted"}
    cart = CartSession.query.get(session["session_id"])
    session["rates_updated"] = False
    return cart.json


@cart_blueprint.route("/api/create_paypal_payment", methods=["GET", "POST"])
def create_paypal_payment():
    cart = CartSession.query.get(session["session_id"])
    payment = create_payment(cart)
    if payment.create():
        return jsonify(payment.to_dict())
    else:
        return payment.error


@cart_blueprint.route("/api/execute_paypal_payment", methods=["POST"])
def execute_paypal_payment():
    payment = paypalrestsdk.Payment.find(request.form["paymentID"])
    if payment.execute({"payer_id": payment["payer"]["payer_info"]["payer_id"]}):
        address = payment["transactions"][0]["item_list"]["shipping_address"]
        buyer = payment["payer"]["payer_info"]
        money = payment["transactions"][0]["amount"]
        transaction_id = payment["transactions"][0]["related_resources"][0]["sale"][
            "id"
        ]
        cart_session = CartSession.query.get(session["session_id"])
        cart_session.convert_order(
            transaction_id,
            order_source="PayPal",
            shipping_service_level=4,
            buyer_first_name=buyer["first_name"],
            buyer_last_name=buyer["last_name"],
            ship_to_address_street=address["line1"],
            ship_to_address_city=address["city"],
            ship_to_address_state=address["state"],
            ship_to_address_zip=address["postal_code"],
            payment_total=money["total"],
        )
    else:
        return payment.error
    return jsonify(dict(redirect=url_for("cart.thank_you", order_id=transaction_id)))


@cart_blueprint.route("/api/amazon/get_details/", methods=["POST"])
def get_amazon_details():
    """
    Sets up Amazon payment. Make sure credentials are good and that site host is approved in the amazon account
    :return: jsonified PayWithAmazon client response
    """
    session["orderReferenceId"] = request.form["orderReferenceId"]
    response = client.get_order_reference_details(
        amazon_order_reference_id=session["orderReferenceId"],
        address_consent_token=session["access_token"],
    )
    return response.to_json()


@cart_blueprint.route("/api/amazon/confirm/", methods=["POST"])
def confirm_amazon_order():
    order_reference_id = session["orderReferenceId"]
    cart_session = CartSession.query.get(session["session_id"])
    set_response = client.set_order_reference_details(
        amazon_order_reference_id=order_reference_id,
        order_total=str(cart_session.total),
        seller_order_id=str(cart_session.id),
        store_name=os.environ.get("STORE_NAME"),
        custom_information="Test Info",
    ).to_json()
    current_app.logger.info(f"Amazon Reference Response: {str(set_response)}")
    confirm_response = client.confirm_order_reference(
        amazon_order_reference_id=order_reference_id
    )
    current_app.logger.info(f"Amazon Confirmation Response: {str(confirm_response)}")
    order_response = client.get_order_reference_details(
        amazon_order_reference_id=order_reference_id,
        address_consent_token=session["access_token"],
    )
    order = cart_session.convert_amazon_order(order_response)
    auth_response = client.authorize(
        amazon_order_reference_id=order_reference_id,
        authorization_reference_id="AMZ" + str(order.id),
        authorization_amount=order.payment_total,
        seller_authorization_note="Authorized",
        transaction_timeout=0,
        capture_now=True,
    )
    current_app.logger.info(f"Amazon Authorization Response: {str(auth_response)}")
    return redirect(url_for("cart.thank_you", order=order.id), code=307)


@cart_blueprint.route("/api/execute_payment", methods=["POST"])
def execute_payment():
    payment = paypalrestsdk.Payment.find(request.form["paymentID"])
    if payment.execute({"payer_id": payment["payer"]["payer_info"]["payer_id"]}):
        address = payment["transactions"][0]["item_list"]["shipping_address"]
        buyer = payment["payer"]["payer_info"]
        money = payment["transactions"][0]["amount"]
        transaction_id = payment["transactions"][0]["related_resources"][0]["sale"][
            "id"
        ]
        cart_session = CartSession.query.get(session["session_id"])
        cart_session.convert_order(
            transaction_id,
            order_source="PayPal",
            shipping_service_level=4,
            buyer_first_name=buyer["first_name"],
            buyer_last_name=buyer["last_name"],
            ship_to_address_street=address["line1"],
            ship_to_address_city=address["city"],
            ship_to_address_state=address["state"],
            ship_to_address_zip=address["postal_code"],
            order_notice_total=money["total"],
        )
    else:
        return payment.error
    return jsonify(
        dict(redirect=url_for("cart.thank_you", order_number_external=transaction_id))
    )


@cart_blueprint.route("/clearsession")
def clear_session():
    session.clear()
    return redirect("/")


@cart_blueprint.context_processor
def cart_credentials():
    return {
        "MWS_ACCESS_KEY": MWS_ACCESS_KEY,
        "AMAZON_CLIENT_ID": AMAZON_CLIENT_ID,
        "SHIPPING_OPTIONS": SHIPPING_OPTIONS,
    }
