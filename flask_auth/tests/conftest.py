# conftest.py
import tempfile
import pytest

from flask_auth.project import create_app, db

# --- bootstrapping import path for pytest ---
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# -------------------------------------------


@pytest.fixture
def app():
    # App de test avec base SQLite temporaire
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,   # faciliter les POST dans les tests
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SERVER_NAME="localhost",  # utile pour url_for dans tests
        SECRET_KEY="test-secret",
    )
    with app.app_context():
        db.create_all()
    yield app
    # Teardown
    with app.app_context():
        db.session.remove()
        db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()