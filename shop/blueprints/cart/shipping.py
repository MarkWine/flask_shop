from dataclasses import dataclass
from decimal import Decimal
import os
from xml.etree import ElementTree as ET

from flask import current_app
import requests

# from requests_futures.sessions import FuturesSession  # if using async requests
import xmltodict
import zeep


ORIGIN_ADDRESS = os.environ.get("ORIGIN_ADDRESS")
USPS_USER_ID = os.environ.get("USPS_USER_ID")
USPS_PASS = os.environ.get("USPS_PASS")
USPS_PRODUCTION_URL = "http://production.shippingapis.com/ShippingAPI.dll"
USPS_SECURE_URL = "https://secure.shippingapis.com/ShippingAPI.dll"
SHIPENGINE_KEY = os.environ.get("SHIPENGINE_KEY")
SHIPENGINE_GET_RATES = os.environ.get("SHIPENGINE_GET_RATES", False)
ENDICIA_ID = os.environ.get("ENDICIA_KEY")
FEDEX_ID = os.environ.get("FEDEX_ID")
FEDEX_KEY = os.environ.get("FEDEX_KEY")
FEDEX_PASS = os.environ.get("FEDEX_PASS")
FEDEX_ACCOUNT = os.environ.get("FEDEX_ACCOUNT")
FEDEX_METER = os.environ.get("FEDEX_METER")

WebAuthenticationDetail = {"UserCredential": {"Key": FEDEX_KEY, "Password": FEDEX_PASS}}
ClientDetail = {"AccountNumber": FEDEX_ACCOUNT, "MeterNumber": FEDEX_METER}
Version = {"Major": 24, "ServiceId": "crs", "Intermediate": 0, "Minor": 0}


@dataclass
class ShippingAddress:
    postal_code: str
    name: str = ""
    phone: str = ""
    company_name: str = ""
    address_line1: str = ""
    address_line2: str = ""
    city: str = "Seattle"
    state: str = "WA"
    country: str = "US"


default_origin = ShippingAddress(ORIGIN_ADDRESS or "98101")


@dataclass
class DestinationAddress(ShippingAddress):
    origin_address: ShippingAddress = ShippingAddress("98101")

    def get_shipengine(self, origin_address=default_origin, weight: int = 1):
        """
        Get rates from shipengine. Because of potential fees, this is avoided unless explicitly invoked
        :param origin_address: 'ShippingAddress'
        :param weight: int ounces
        :return:
        """
        rate_url = "https://api.shipengine.com/v1/rates"
        headers = {"Content-type": "application/json", "api-key": SHIPENGINE_KEY}

        ship_data = {
            "shipment": {
                "validate_address": "no_validation",
                "ship_to": {
                    "postal_code": self.postal_code,
                    "country_code": self.country,
                },
                "ship_from": {
                    "name": origin_address.name,
                    "phone": origin_address.phone,
                    "company_name": origin_address.company_name,
                    "address_line1": origin_address.address_line1,
                    "address_line2": origin_address.address_line2,
                    "city_locality": origin_address.city,
                    "state_province": origin_address.state,
                    "postal_code": origin_address.postal_code,
                    "country_code": origin_address.country,
                },
                "packages": [{"weight": {"value": weight, "unit": "ounce"}}],
            },
            "rate_options": {"carrier_ids": [FEDEX_ID, ENDICIA_ID]},
        }
        rate_json = requests.post(rate_url, headers=headers, json=ship_data).json()
        rate_values = [
            {
                "service": rate.get("service_code"),
                "rate": rate.get("shipping_amount").get("amount"),
            }
            for rate in rate_json["rate_response"]["invalid_rates"]
        ]
        return rate_values

    def request_usps_domestic(self, weight, origin_address=default_origin):
        """
        Structure and send request for USPS rates
        :param weight: in oz
        :type origin_address: 'ShippingAddress'
        :return: Ordered Dict of services and rates
        """
        print(self.postal_code)
        print(weight)
        print(origin_address.postal_code)
        request_xml = ET.Element("RateV4Request")
        request_xml.attrib = {"USERID": str(USPS_USER_ID)}

        ET.SubElement(request_xml, "Revision").text = "2"

        package_xml = ET.SubElement(request_xml, "Package")
        package_xml.attrib = {"ID": "EX158"}

        ET.SubElement(package_xml, "Service").text = "ALL"
        ET.SubElement(package_xml, "FirstClassMailType").text = "ALL"
        ET.SubElement(package_xml, "ZipOrigination").text = str(
            origin_address.postal_code or "98101"
        )
        ET.SubElement(package_xml, "ZipDestination").text = str(
            self.postal_code or "66606"
        )
        ET.SubElement(package_xml, "Pounds").text = "0"
        ET.SubElement(package_xml, "Ounces").text = str(weight)
        ET.SubElement(package_xml, "Container")
        ET.SubElement(package_xml, "Size").text = "Regular"
        ET.SubElement(package_xml, "Machinable").text = "true"
        data_xml = {"API": "RateV4", "XML": ET.tostring(request_xml, "unicode")}

        results = requests.post(url=USPS_PRODUCTION_URL, data=data_xml)
        return results

    def get_usps_domestic(self, weight: int = 1):
        """
        Take result from usps api call and output rate data as dict
        :return:
        """
        try:
            parsed_results = xmltodict.parse(
                self.request_usps_domestic(weight).content
            )["RateV4Response"]["Package"]["Postage"]
            priority = next(
                (
                    Decimal(service["Rate"])
                    for service in parsed_results
                    if service["@CLASSID"] == "1"
                ),
                None,
            )
            first_class = next(
                (
                    Decimal(service["Rate"])
                    for service in parsed_results
                    if service["MailService"]
                    == "First-Class Package Service - Retail&lt;sup&gt;&#8482;&lt;/sup&gt;"  # Get Better Identifiers
                ),
                None,
            )
            rates = {"USPS_PRIORITY": priority, "USPS_FIRST_CLASS": first_class}
        except KeyError:
            rates = {"USPS_PRIORITY": None, "USPS_FIRST_CLASS": None}
        return rates

    def get_fedex_rates(self, origin_address=default_origin, weight=1.0):
        """
        Get FedEx Rates using webservices
        :param origin_address: 'ShippingAddress'
        :param weight:
        :return:
        """
        fedex_client = zeep.Client(
            current_app.open_instance_resource("RateService_v24.wsdl")
        )
        requested_shipment = {
            "Shipper": {
                "Address": {
                    "PostalCode": origin_address.postal_code,
                    "CountryCode": origin_address.country,
                    "StateOrProvinceCode": origin_address.state,
                }
            },
            "Recipient": {
                "Address": {
                    "PostalCode": self.postal_code or 32703,
                    "CountryCode": self.country or "US",
                    # "StateOrProvinceCode": self.state or "FL",
                }
            },
            "RequestedPackageLineItems": {
                "Weight": {"Units": "LB", "Value": weight},
                "GroupPackageCount": 1,
            },
            "PackageCount": 1,
        }
        try:
            rate_request = fedex_client.service.getRates(
                WebAuthenticationDetail=WebAuthenticationDetail,
                ClientDetail=ClientDetail,
                Version=Version,
                RequestedShipment=requested_shipment,
            )
            ground_rate = [
                reply
                for reply in rate_request["RateReplyDetails"]
                if reply["ServiceType"] == "FEDEX_GROUND"
            ]
            ground_rate_value = ground_rate[0]["RatedShipmentDetails"][0][
                "ShipmentRateDetail"
            ]["TotalNetFedExCharge"]["Amount"]
        except (IndexError, zeep.exceptions.ValidationError):
            ground_rate_value = None
        return {"FEDEX_GROUND": ground_rate_value}
