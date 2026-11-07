import pytest
from flask import Flask

from models import db, init_db, User, Folder


def _make_app(db_uri):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    init_db(app)
    return app


@pytest.fixture
def app(monkeypatch, tmp_path):
    import config

    monkeypatch.setattr(config, "DEFAULT_ADMIN_USERNAME", "root")
    monkeypatch.setattr(config, "DEFAULT_ADMIN_EMAIL", "root@example.com")
    monkeypatch.setattr(config, "DEFAULT_ADMIN_PASSWORD", "s3cret-pass")

    app = _make_app(f"sqlite:///{tmp_path / 'test.db'}")
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


def test_password_is_hashed_and_verifiable():
    user = User(username="alice", email="alice@example.com", password="pw-123456")
    assert user.password_hash != "pw-123456"
    assert user.check_password("pw-123456")
    assert not user.check_password("wrong")


@pytest.mark.parametrize(
    "role, upload, manage_users",
    [("viewer", False, False), ("uploader", True, False), ("admin", True, True)],
)
def test_role_permissions(role, upload, manage_users):
    user = User(username="u", email="u@example.com", password="pw-123456")
    user.role = role
    assert user.can_upload() is upload
    assert user.can_manage_documents() is upload
    assert user.can_manage_folders() is upload
    assert user.can_manage_users() is manage_users
    assert user.is_admin is manage_users
    assert user.can_search() is True


def test_init_db_creates_configured_admin_and_default_folder(app):
    admin = User.query.filter_by(username="root").one()
    assert admin.role == "admin"
    assert admin.email == "root@example.com"
    assert admin.check_password("s3cret-pass")
    assert Folder.query.filter_by(user_id=admin.id, name="Uncategorized").count() == 1


def test_init_db_is_idempotent(app):
    # A second start-up against the same database must not duplicate the admin.
    second = _make_app(app.config["SQLALCHEMY_DATABASE_URI"])
    with second.app_context():
        assert User.query.filter_by(username="root").count() == 1
