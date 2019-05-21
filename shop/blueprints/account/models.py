from flask_security import RoleMixin, UserMixin

from shop import db


class AccountUser(db.Model, UserMixin):
    __tablename__ = "account_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)

    account_roles = db.relationship('AccountRole', secondary='roles_users')


class AccountRole(db.Model, RoleMixin):
    __tablename__ = "account_roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Integer, unique=True)


class RoleUsers(db.Model):
    __tablename__ = "roles_users"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("account_users.id"))
    role_id = db.Column(db.Integer, db.ForeignKey("account_roles.id"))


class WishList(db.Model):
    __tablename__ = "wishlist_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("account_users.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
