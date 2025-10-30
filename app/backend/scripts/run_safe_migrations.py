"""Run dedupe helper and then run Alembic migrations safely.

Usage:
  python backend/scripts/run_safe_migrations.py         # dry-run: show dedupe summary
  python backend/scripts/run_safe_migrations.py --apply # apply dedupe and run alembic upgrade head

This script imports the dedupe helper and runs it programmatically, then runs Alembic upgrade.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app, db
from alembic.config import Config
from alembic import command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply dedupe and run migrations')
    args = parser.parse_args()

    # initialize DB integration
    db.init_app(app)
    with app.app_context():
        # Import dedupe helper functions lazily so they use the initialized DB
        try:
            from backend.scripts.dedupe_xp_events import dry_run, apply_actions, reconcile_users
        except Exception as e:
            print('Failed to import dedupe helper:', e)
            return

        session = db.session
        actions = dry_run(session)
        total = sum(len(rem) for (_k, _key, _keep, rem) in actions)
        print(f"Dedupe dry-run: total duplicate rows identified = {total}")

        if not args.apply:
            print('\nDry-run complete. Re-run with --apply to remove duplicates and run Alembic migrations.')
            return

        print('\nApplying duplicate removals...')
        removed = apply_actions(session, actions)
        session.commit()
        print(f'Removed {len(removed)} xp_event rows')

        print('Reconciling users xp_total/levels...')
        updates = reconcile_users(session)
        session.commit()
        print(f'Updated {len(updates)} users')

        # Run alembic upgrade
        print('Running Alembic upgrade head...')
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
        # ensure SQLAlchemy URL is read from env if provided
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if db_url:
            alembic_cfg.set_main_option('sqlalchemy.url', db_url)
        command.upgrade(alembic_cfg, 'head')
        print('Alembic upgrade complete.')


if __name__ == '__main__':
    main()
