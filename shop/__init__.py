import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import SQLAlchemySessionUserDatastore, Security
from sqlalchemy_utils import database_exists, create_database


app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py", silent=True)

# Sif not database_exists(app.config.get("SQLALCHEMY_DATABASE_URI")):
#     create_database(app.config.get("SQLALCHEMY_DATABASE_URI"))
db = SQLAlchemy(app)

from .blueprints.cart.views import cart_blueprint
from .blueprints.admin.views import admin_blueprint
from .blueprints.products.views import product_blueprint
from .blueprints.orders.views import order_blueprint
from .blueprints.account.views import account_blueprint
from .blueprints.categories.views import category_blueprint
from .blueprints.static_pages.views import static_blueprint


app.register_blueprint(static_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(cart_blueprint)
app.register_blueprint(product_blueprint)
app.register_blueprint(account_blueprint)
app.register_blueprint(category_blueprint)
app.register_blueprint(order_blueprint)

from .blueprints.account.models import AccountUser, AccountRole
from .blueprints.account.forms import RegistrationForm, LoginForm

try:
    AccountUser.query.first()
except Exception as e:
    db.create_all()

user_datastore = SQLAlchemySessionUserDatastore(db.session, AccountUser, AccountRole)
security = Security(
    app, user_datastore, register_form=RegistrationForm, login_form=LoginForm
)
