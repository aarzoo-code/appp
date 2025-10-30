# Backend (Gamification API)

This is a minimal Flask backend used for the gamification MVP. It defaults to SQLite for local development.

Quick start (dev):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py
```

The API will be available at http://localhost:5000.

Migrations (Alembic)
--------------------

This project includes Alembic migration scripts under `backend/alembic/`.

To run migrations locally (requires `alembic` in your environment):

```bash
# from repo root
PYTHONPATH=$(pwd) alembic -c backend/alembic.ini upgrade head
```

If you don't have a running Postgres/Redis for local development, the project will still work with the lightweight `run_migrations.py` which calls `db.create_all()` (good for tests/dev):

```bash
python backend/run_migrations.py
```

Redis (rate limiting)
----------------------

The XP award endpoint supports a Redis-backed rate limiter. Configure a Redis URL via the `REDIS_URL` environment variable (default `redis://localhost:6379/0`). If Redis is not available the app falls back to an in-memory rate limiter (per-process, not suitable for production).

To enable Redis locally (example using Docker):

```bash
docker run -p 6379:6379 --name local-redis -d redis:7
export REDIS_URL=redis://localhost:6379/0
```

Then run the app as above.

Deduplication helper
--------------------

If you are applying the Alembic migration that adds unique constraints to `xp_events` in a production DB, first run the dedupe script to identify (and optionally remove) duplicates.

Dry-run (safe):

```bash
python backend/scripts/dedupe_xp_events.py
```

Apply removals and reconcile users' XP totals:

```bash
python backend/scripts/dedupe_xp_events.py --apply
```

CAUTION: always back up your production DB before running with `--apply`.

Endpoints:
- GET `/health`
- GET `/api/v1/ping`
- POST `/api/v1/users` — create user
- GET `/api/v1/users/:id/stats` — fetch user stats
- POST `/api/v1/xp/award` — award XP to user
- GET `/api/v1/leaderboard` — fetch top users
- GET `/api/v1/me/progress` — fetch authenticated user's progress (xp, level, streak, recent events, badges)

`GET /api/v1/me/progress`

Response (200):

{
	"ok": true,
	"user": { ... },          # user summary (id, display_name, email, xp_total, level, created_at)
	"streak": {              # optional
		"current_streak": 5,
		"last_checkin_date": "2025-10-30"
	},
	"recent_events": [       # last 10 XP events
		{"id": 1, "amount": 50, "source": "challenge", "created_at": "..."}
	],
	"badges": [              # earned badges
		{"id": 2, "code": "first_steps", "name": "First Steps", "earned_at": "..."}
	],
	"xp": 1500,
	"level": 3,
	"xp_to_next": 500,
	"next_level_threshold": 2000,
	"level_progress_percent": 75
}

Authorization: requires Bearer token returned from `/api/v1/auth/signup` or `/api/v1/auth/login`.

Notes:
- For production use a Postgres `DATABASE_URL` and run migrations via Alembic (not included in scaffold).
