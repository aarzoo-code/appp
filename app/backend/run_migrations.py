"""Run simple SQLAlchemy create_all for dev environment.
This is a lightweight replacement for alembic migrations for local dev.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app, db

with app.app_context():
    db.create_all()
    print('Created all tables using SQLAlchemy create_all()')
