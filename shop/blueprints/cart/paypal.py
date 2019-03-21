import os

from flask import url_for, session
import paypalrestsdk

PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")
CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")

paypalrestsdk.configure(
    {"mode": PAYPAL_MODE, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
)


def create_payment(cart):
    payment = paypalrestsdk.Payment(
        {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": url_for("thank_you"),
                "cancel_url": url_for("shopping_cart"),
            },
            "transactions": [
                {
                    "amount": {"total": str(cart.cart_total), "currency": "USD"},
                    "description": "This is the payment transaction description.",
                }
            ],
        }
    )
