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
)

from shop import db
from .models import CartSession, CartItem
from .amazon import client
from ..orders.models import Order

cart_blueprint: Blueprint = Blueprint(
    name="cart", import_name=__name__, template_folder="templates"
)


@cart_blueprint.route("/cart")
def cart():
    if 'session_id' not in session:
        cart_session = CartSession()
        db.session.add(cart_session)
        db.session.commit()
        session['session_id'] = cart_session.id
    try:
        cart_session = CartSession.query.get(session["session_id"])
    except (KeyError, ValueError):
        return render_template("error", message="Nothing in your cart yet!")
    return render_template("cart.html", cart_session=cart_session)


@cart_blueprint.route("/checkout")
def checkout():
    return render_template("checkout.html")


@cart_blueprint.route("/thankyou")
def thankyou_page():
    order = Order.query.get(request.args.get("order_id"))
    return render_template("thankyou.html", order=order)


@cart_blueprint.route("/api/update_zipcode")
def update_zipcode():
    cart = CartSession.query.get(session["session_id"])
    pass


@cart_blueprint.route("/api/update_quantity")
def update_quantity():
    pass


@cart_blueprint.route("/api/remove_item")
def remove_item():
    try:
        item = CartItem.query.get(request.json.get("item_id"))
        item.delete()
        db.session.commit()
    except KeyError:
        return {"Item already deleted"}

    pass


@cart_blueprint.route("/api/amazon/get_details/", methods=["POST"])
def get_amazon_details():
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
    try:
        confirm_result = json.loads(order_response.to_json())[
            "GetOrderReferenceDetailsResponse"
        ]["GetOrderReferenceDetailsResult"]["OrderReferenceDetails"]
    except KeyError:
        return "Order Not Confirmed by Amazon"
    address = confirm_result["Destination"]["PhysicalDestination"]
    cart_session.convert_order(
        confirm_result.get("AmazonOrderReferenceId"),
        payment_type="PayWithAmazon",
        shipping_service_level="None",
        buyer_first_name=confirm_result["Buyer"]["Name"],
        buyer_last_name=confirm_result["Buyer"]["Name"],
        ship_address_=address["AddressLine1"],
        ship_address2=address.get("AddressLine2", ""),
        ship_city=address["City"],
        ship_state=address["StateOrRegion"],
        ship_postal_code=address["PostalCode"],
        ship_country=address.get("CountryCode"),
        order__total=confirm_result["OrderTotal"]["Amount"],
    )
    order = Order.query.filter(Order.cart_id == session["session_id"])
    auth_response = client.authorize(
        amazon_order_reference_id=order_reference_id,
        authorization_reference_id="AMZ" + str(order.id),
        authorization_amount=order.payment_total,
        seller_authorization_note="Authorized",
        transaction_timeout=0,
        capture_now=True,
    )
    current_app.logger.info(f"Amazon Authorization Response: {str(auth_response)}")
    return redirect(url_for("thank_you", order=order.id), code=307)
