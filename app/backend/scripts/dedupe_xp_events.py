"""Deduplicate XP events and reconcile user xp_total.

Usage:
  python backend/scripts/dedupe_xp_events.py         # dry-run, prints summary
  python backend/scripts/dedupe_xp_events.py --apply # actually delete duplicates and reconcile

This script finds duplicates in two ways:
  1) same (user_id, source, source_id) when both source and source_id are set
  2) same (user_id, idempotency_key) when idempotency_key is set

It keeps the earliest event (by created_at) and removes later duplicates.
After removals (when --apply is used) it recalculates each user's xp_total as the
sum of their remaining XPEvent.amount values and updates level accordingly.

CAUTION: run with --apply only after taking a DB backup in production.
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app, db
from backend.models import XPEvent, User
from sqlalchemy import text
from backend.schemas import compute_new_level


def find_duplicate_groups(session):
    # Find duplicates by (user_id, source, source_id) where both source and source_id are not null
    try:
        dup_source = session.execute(
            text(
                """
        SELECT user_id, source, source_id, COUNT(*) as cnt
        FROM xp_events
        WHERE source IS NOT NULL AND source_id IS NOT NULL
        GROUP BY user_id, source, source_id
        HAVING cnt > 1
        """
            )
        ).fetchall()
    except Exception as e:
        print('Warning: could not run source-based duplicate query:', e)
        dup_source = []

    # Find duplicates by (user_id, idempotency_key) where idempotency_key is not null
    try:
        dup_idemp = session.execute(
            text(
                """
        SELECT user_id, idempotency_key, COUNT(*) as cnt
        FROM xp_events
        WHERE idempotency_key IS NOT NULL
        GROUP BY user_id, idempotency_key
        HAVING cnt > 1
        """
            )
        ).fetchall()
    except Exception as e:
        # likely the column doesn't exist in older DBs
        print('Info: idempotency_key column not present or query failed; skipping idempotency duplicates:', e)
        dup_idemp = []

    return dup_source, dup_idemp


def collect_rows_for_group(session, kind, key):
    # kind: 'source' -> key = (user_id, source, source_id)
    # kind: 'idemp' -> key = (user_id, idempotency_key)
    if kind == 'source':
        user_id, source, source_id = key
        rows = session.execute(
            text(
                """
            SELECT id, amount, created_at
            FROM xp_events
            WHERE user_id = :uid AND source = :source AND source_id = :source_id
            ORDER BY created_at ASC, id ASC
            """
            ),
            {'uid': user_id, 'source': source, 'source_id': source_id}
        ).fetchall()
    else:
        user_id, idemp = key
        rows = session.execute(
            text(
                """
            SELECT id, amount, created_at
            FROM xp_events
            WHERE user_id = :uid AND idempotency_key = :idemp
            ORDER BY created_at ASC, id ASC
            """
            ),
            {'uid': user_id, 'idemp': idemp}
        ).fetchall()
    return rows


def dry_run(session):
    dup_source, dup_idemp = find_duplicate_groups(session)
    total_dup = 0
    actions = []

    print(f"Found {len(dup_source)} duplicate groups by (user,source,source_id)")
    print(f"Found {len(dup_idemp)} duplicate groups by (user,idempotency_key)")

    for row in dup_source:
        key = (row.user_id, row.source, row.source_id)
        rows = collect_rows_for_group(session, 'source', key)
        keep = rows[0]
        remove = rows[1:]
        total_dup += len(remove)
        actions.append(('source', key, keep, remove))

    for row in dup_idemp:
        key = (row.user_id, row.idempotency_key)
        rows = collect_rows_for_group(session, 'idemp', key)
        keep = rows[0]
        remove = rows[1:]
        total_dup += len(remove)
        actions.append(('idemp', key, keep, remove))

    print(f"Total duplicate event rows that would be removed: {total_dup}")
    return actions


def apply_actions(session, actions):
    removed_ids = []
    for kind, key, keep, remove in actions:
        ids = [r.id for r in remove]
        if not ids:
            continue
        # Use ORM delete to avoid param style issues
        session.query(XPEvent).filter(XPEvent.id.in_(ids)).delete(synchronize_session=False)
        removed_ids.extend(ids)
    return removed_ids


def reconcile_users(session):
    # Recalculate xp_total per user and update level
    users = session.execute("SELECT id FROM users").fetchall()
    updates = []
    for u in users:
        uid = u.id
        s = session.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM xp_events WHERE user_id = :uid",
            {'uid': uid}
        ).fetchone()
        total = int(s.total or 0)
        level = compute_new_level(total)
        session.execute(
            "UPDATE users SET xp_total = :total, level = :level WHERE id = :uid",
            {'total': total, 'level': level, 'uid': uid}
        )
        updates.append((uid, total, level))
    return updates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply deletions and reconcile users')
    args = parser.parse_args()

    # Ensure the SQLAlchemy instance is initialized with the Flask app
    db.init_app(app)
    with app.app_context():
        session = db.session
        actions = dry_run(session)
        if not args.apply:
            print('\nDry-run complete. Re-run with --apply to remove duplicates and reconcile users.')
            return

        print('\nApplying duplicate removals...')
        removed = apply_actions(session, actions)
        session.commit()
        print(f'Removed {len(removed)} xp_event rows')

        print('Reconciling users xp_total and levels...')
        updates = reconcile_users(session)
        session.commit()
        print(f'Updated {len(updates)} users')
        print('Done.')


if __name__ == '__main__':
    main()
