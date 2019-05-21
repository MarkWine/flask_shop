from decimal import Decimal
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


from shop.blueprints.account.models import AccountUser, AccountRole, RoleUsers
from shop.blueprints.products.models import Product
from shop.blueprints.cart.models import CartSession, CartItem
from shop.blueprints.categories.models import Category, ProductCategory, Filter, FilterProduct, FilterOptions

pytest_plugins = ['pytest-flask-sqlalchemy']


@pytest.fixture(scope='session')
def app():
    from shop import app as test_app
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return test_app


@pytest.fixture(scope='session')
def client_test(app):
    client_test = app.test_client()
    yield client_test


@pytest.fixture(scope='session')
def _db(app, request):
    from shop import db as _db
    with app.test_request_context():
        _db.drop_all()
        _db.create_all()

    @request.addfinalizer
    def drop_database():
        _db.drop_all()
    return _db

@pytest.fixture
def product_test(db_session):
    product_test = Product(name='product_test',
                           weight=Decimal(0.1),
                           price=Decimal('2.13'))
    db_session.add(product_test)
    db_session.commit()
    return product_test


@pytest.fixture
def product_test_heavy(db_session):
    product_test_heavy = Product(name='product_test_heavy',
                           weight=Decimal(40),
                           price=Decimal('10.13'))
    db_session.add(product_test_heavy)
    db_session.commit()
    return product_test_heavy


@pytest.fixture
def category_test(db_session):
    category_test = Category(name='category_test')
    db_session.add(category_test)
    db_session.commit()
    return category_test


@pytest.fixture
def product_category_test(db_session, product_test, category_test):
    product_category_test = ProductCategory(product_id=product_test.id,
                                            category_id=category_test.id)
    db_session.add(product_category_test)
    db_session.commit()
    return product_category_test


@pytest.fixture
def filter_test(db_session):
    filter_test = Filter(name='test_filter')
    db_session.add(filter_test)
    db_session.commit()

    return filter_test


@pytest.fixture
def filter_options_test(db_session, filter_test):
    filter_test_option_1 = FilterOptions(filter_id=filter_test.id, name='test_option_1')
    db_session.add(filter_test_option_1)
    filter_test_option_2 = FilterOptions(filter_id=filter_test.id, name='test_option_2')
    db_session.add(filter_test_option_2)
    db_session.commit()

    return filter_test_option_1, filter_test_option_2

@pytest.fixture
def filter_product_test(db_session, filter_options_test, product_test):
    filter_product_test=FilterProduct(product_id=product_test.id,
                                      filter_option_id=filter_options_test[0].id)
    db_session.add(filter_product_test)
    db_session.commit()
    return filter_product_test


@pytest.fixture
def cart_test(app, db_session, product_test, client_test):
    cart_test = CartSession()
    db_session.add(cart_test)
    db_session.commit()

    cart_item_1 = CartItem(product_id=product_test.id,
                           cart_id=cart_test.id)
    db_session.add(cart_item_1)

    db_session.commit()
    with client_test.session_transaction() as sess:
        sess['session_id'] = cart_test.id
    return cart_test


@pytest.fixture
def cart_item_test(db_session, cart_test, product_test_heavy):
    cart_item_test = CartItem(product_id=product_test_heavy.id,
                              cart_id=cart_test.id,
                              quantity=2)
    db_session.add(cart_item_test)
    db_session.commit()
    return cart_item_test


@pytest.fixture
def role_test(db_session):
    role_test = AccountRole(name='Test Role')
    db_session.add(role_test)
    db_session.commit()
    return role_test


@pytest.fixture
def account_test(db_session, role_test):
    account_test = AccountUser()
    db_session.add(account_test)
    db_session.commit()

    role_user_test = RoleUsers(user_id=account_test.id,
                               role_id=role_test.id)
    db_session.add(role_user_test)
    db_session.commit()
    return account_test
