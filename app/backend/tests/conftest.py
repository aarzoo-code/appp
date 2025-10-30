import os
import sys
import tempfile

# ensure repo root on path when running tests directly
# conftest may be executed from different CWDs; make the path insertion robust
# - file: app/backend/tests/conftest.py
# - desired import root: project `app/` directory so `import backend` works
this_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(this_file)
backend_dir = os.path.dirname(tests_dir)
project_root = os.path.dirname(backend_dir)
# insert project_root (app/) and backend_dir as fallbacks
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from backend.app import app, db
from backend.models import User


@pytest.fixture(scope='module')
def test_client():
    # Use an in-memory SQLite DB for tests
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    # initialize DB for this test instance (guard if already initialized)
    try:
        db.init_app(app)
    except RuntimeError:
        # already initialized by another test module; that's OK
        pass
    with app.app_context():
        db.create_all()
        # create a sample user
        u = User(display_name='TestUser')
        db.session.add(u)
        db.session.commit()

    with app.test_client() as client:
        yield client
