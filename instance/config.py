import os

SQLALCHEMY_DATABASE_URI = (
    os.environ.get("SQLALCHEMY_DATABASE_URI")
    or os.environ.get("DATABASE_URL")  # default Heroku variable
    or "sqlite:///:memory:"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "howdy"
NO_PRODUCT = True
