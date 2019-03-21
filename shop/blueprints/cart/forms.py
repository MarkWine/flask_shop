from wtforms import (
    BooleanField,
    StringField,
    SelectField,
    PasswordField,
    TextAreaField,
    validators,
)
from flask_wtf import FlaskForm


class AddressForm(FlaskForm):
    address_name = StringField("Address Nickname", validators=[validators.Optional()])
    first = StringField("First Name", validators=[validators.InputRequired()])
    last = StringField("Last Name")
    address = StringField("Address", validators=[validators.InputRequired])
    address_2 = StringField(
        "Address Line 2 (optional)", validators=[validators.Optional()]
    )
    email = StringField("Email Address", validators=[validators.InputRequired()])
    state = StringField("State/Province", validators=[validators.Length(min=2)])
    zip = StringField("Zip/Postal Code", validators=[validators.InputRequired()])


class CheckoutForm(FlaskForm):
    billing_country = SelectField(
        "Country",
        choices=[("US", "United States"), ("Can", "Canada"), ("AUS", "Australia")],
    )
    billing_first = StringField("First Name", validators=[validators.InputRequired()])
    billing_last = StringField("Last Name", validators=[validators.Optional()])
    billing_address = StringField(
        "Address", validators=[validators.Length(min=1, max=35)]
    )
    billing_address_2 = StringField(
        "Address Line 2 (optional)", validators=[validators.Optional()]
    )
    billing_city = StringField("City", validators=[validators.InputRequired()])
    billing_state = SelectField(
        "State/Province", choices=[("WA", "Washington", ("CA", "California"))]
    )
    billing_zip = StringField(
        "Zip/Postal Code", validators=[validators.InputRequired()]
    )
    shipping_billing = BooleanField("Ship to Billing Address?")
    shipping_country = SelectField(
        "Country",
        choices=[("US", "United States"), ("Can", "Canada"), ("AUS", "Australia")],
    )
    shipping_first = StringField("First Name", validators=[validators.InputRequired()])
    shipping_last = StringField("Last Name", validators=[validators.Optional()])
    shipping_address = StringField(
        "Address", validators=[validators.Length(min=1, max=35)]
    )
    shipping_address_2 = StringField(
        "Address Line 2 (optional)", validators=[validators.Optional()]
    )
    shipping_city = StringField("City", validators=[validators.InputRequired()])
    shipping_state = SelectField(
        "State/Province", choices=[("WA", "Washington"), ("CA", "California")]
    )
    shipping_zip = StringField(
        "Zip/Postal Code", validators=[validators.InputRequired()]
    )
    shipping_phone = StringField(
        "Phone (Recipient)", validators=[validators.InputRequired()]
    )
    contact_email = StringField(
        "E-mail Address",
        validators=[
            validators.Email("Invalid E-mail Address"),
            validators.EqualTo("email_confirm", "E-mail Addresses Must Match"),
        ],
    )
    email_confirm = StringField(
        "E-mail Address", validators=[validators.Email("Invalid E-mail Address")]
    )
    phone_number = StringField("Phone Number", validators=[validators.InputRequired()])
