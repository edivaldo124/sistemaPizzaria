import os

os.environ.setdefault('SECRET_KEY', 'chave-de-teste')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('COOKIE_SECURE', 'false')
os.environ.setdefault('RATELIMIT_STORAGE_URI', 'memory://')

import pytest

from servidor import app as flask_app
from config import db as _db


@pytest.fixture()
def app():
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db(app):
    return _db
