# Deployment Guide

This document describes how to deploy the `appp` stack using the included CI workflow and the `docker-compose` setup.

## Overview
- CI builds and tests the backend and frontend.
- CI builds and pushes Docker images to GitHub Container Registry (GHCR).
- CI can sync `docker-compose.yml` to a remote host and run `docker-compose up -d` there (via SSH).

## Required GitHub secrets
Add these repository secrets under Settings -> Secrets:

- `GHCR_PAT` - Personal access token with `write:packages` (or use a token with package:write). Used to push/pull images to GHCR.
- `DEPLOY_HOST` - Hostname or IP of the remote server (example: `203.0.113.5`).
- `DEPLOY_USER` - SSH user (that can run Docker commands on the remote host).
- `DEPLOY_SSH_KEY` - Private SSH key for the `DEPLOY_USER` with access to the remote host.
- `DEPLOY_PORT` - (optional) SSH port on the remote host (default: 22). Set to `22` if unset.

Make sure the `DEPLOY_USER` is in the `docker` group or can run Docker commands via sudo without a password.

## Remote host setup
On the remote server (example path `/srv/appp`):

1. Install Docker and Docker Compose.
2. Create the deployment directory and ensure correct permissions:

```bash
sudo mkdir -p /srv/appp
sudo chown $USER:$USER /srv/appp
```

3. (Optional) If you want to keep environment variables outside of `docker-compose.yml`, create an `.env` file in `/srv/appp` and add it to `.gitignore` locally. The CI currently copies only `docker-compose.yml` — you can rsync `.env` manually or extend CI to copy it as well.

## How CI deploy works
- On push to `main`, CI will run tests, build & push Docker images to GHCR, then sync `app/docker-compose.yml` to `/srv/appp/docker-compose.yml` on the remote host, then SSH into the host and run `docker-compose up -d --remove-orphans`.
- The CI deploy step authenticates to GHCR on the remote host using the `GHCR_PAT` secret (piped into `docker login`).

### Automatic migrations during deploy
- The CI `deploy` job now runs Alembic migrations on the remote host after bringing up the stack.
- When using `docker-compose`, the deploy job runs:
	- `docker-compose -f /srv/appp/docker-compose.yml run --rm web alembic -c backend/alembic.ini upgrade head`
	- If that fails, it attempts to `docker exec` into the running `web` container and run the migrations there.
- When using the fallback `docker run` flow (no docker-compose file present), the deploy job will start a container named `appp_web` and attempt `docker exec appp_web alembic -c backend/alembic.ini upgrade head`.

Notes:
- Ensure the database connection environment variable (e.g., `DATABASE_URL`) is present in the `docker-compose.yml` or set on the remote host so Alembic can connect to the DB.
- Migrations are run non-interactively; for production use, consider a migration window or manual review on major schema changes.

### Manual approval and automatic backups

- The `deploy` job is configured to use the `production` environment. If you configure environment protection rules in GitHub (required reviewers), the deploy will pause for manual approval before executing. This provides a safe gate for production migrations.
- Before running migrations, the deploy job attempts a best-effort backup of the PostgreSQL database if your `docker-compose.yml` defines a `postgres` service:
	- It writes a timestamped SQL dump to `/srv/appp/backups/backup-YYYYMMDDHHMMSS.sql` on the remote host using `pg_dumpall` from the `postgres` service.
	- If no `postgres` service exists in the compose file, the job will skip the automatic backup and proceed (you should ensure backups via other means).

Notes:
- The backup step is best-effort and expects a `postgres` service in the compose file. For managed DBs or different setups, ensure you provide a backup method (e.g., managed DB snapshot) prior to running migrations.
- Consider automating off-site backups and retention policies.

## Local deployment (development/testing)
You can also deploy locally using the included scripts.

Start the stack locally (build images and run):

```bash
cd app
./scripts/deploy_local.sh up
```

Stop:

```bash
cd app
./scripts/deploy_local.sh down
```

Rebuild images locally:

```bash
cd app
./scripts/deploy_local.sh build
```

## Notes & best practices
- For production, consider using a registry user that has limited permissions and rotate tokens regularly.
- Consider allowing the CI to rsync the `.env` file (if you store environment variables in a file) — be careful not to leak secrets in build logs.
- Consider adding health checks and readiness probes for zero-downtime deploys.
- For more robust deployments, consider Kubernetes, ECS, or a managed platform.

If you want, I can add an optional CI step to securely copy an `.env` file as well (requires that you add the `.env` file contents as a GitHub secret and write it out on the remote host).