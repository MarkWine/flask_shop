import os

from flask import url_for, session
import paypalrestsdk

PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")

paypalrestsdk.configure(
    {
        "mode": PAYPAL_MODE,
        "client_id": PAYPAL_CLIENT_ID,
        "client_secret": PAYPAL_CLIENT_SECRET,
    }
)


def create_payment(cart):
    """
    Create a Paypal payment based on cart data
    :param cart: CartSession
    :return: paypalrestsdk.Payment
    """
    payment = paypalrestsdk.Payment(
        {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": url_for("thank_you_page"),
                "cancel_url": url_for("cart_page"),
            },
            "transactions": [
                {
                    "amount": {"total": str(cart.cart_total), "currency": "USD"},
                    "description": f"This is the payment for session {session.get('session_id', 'Unknown')}.",
                }
            ],
        }
    )
    return payment
