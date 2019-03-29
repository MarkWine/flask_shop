import os

SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///:memory:"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "howdy"
