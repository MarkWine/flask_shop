from flask_security.forms import RegisterForm, LoginForm
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, validators


class RegistrationForm(RegisterForm):
    first = StringField("First Name", [validators.InputRequired()])
    last = StringField("Last Name", [validators.InputRequired()])
    email = StringField("Email Address", [validators.InputRequired])
    password = PasswordField("Password", [validators.Length(min=5, max=35)])
    accept_rules = BooleanField("I accept the site rules", [validators.InputRequired()])


class LoginForm(LoginForm):
    email = StringField("Email", validators=[validators.InputRequired()])
    password = PasswordField("Password", [validators.Length(min=5, max=35)])
