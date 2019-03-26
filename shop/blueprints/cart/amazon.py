from pay_with_amazon.client import PayWithAmazonClient
import os

MWS_ACCESS_KEY = os.environ.get("MWS_ACCESS_KEY", "")
MWS_SECRET_KEY = os.environ.get("MWS_SECRET_KEY", "")
MERCHANT_ID = os.environ.get("MERCHANT_ID", "")
AMAZON_CLIENT_ID = os.environ.get("AMAZON_CLIENT_ID")
MWS_SANDBOX = os.environ.get("MWS_SANDBOX", True)

client = PayWithAmazonClient(
    mws_access_key=MWS_ACCESS_KEY,
    mws_secret_key=MWS_SECRET_KEY,
    merchant_id=MERCHANT_ID,
    region="na",
    currency_code="USD",
    sandbox=MWS_SANDBOX,
)
