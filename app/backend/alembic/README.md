This folder contains Alembic migration environment.

Use the following commands from the `backend` directory after activating your venv:

```bash
alembic -c alembic.ini revision --autogenerate -m "create initial tables"
alembic -c alembic.ini upgrade head
```

Note: The `sqlalchemy.url` in `alembic.ini` defaults to the SQLite dev DB. For Postgres, set `sqlalchemy.url` or `DATABASE_URL` env var before running migrations.
