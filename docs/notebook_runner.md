# Notebook Runner (Design & Scaffold)

This document describes the minimal notebook/job runner scaffold included in the project and next steps to make it production-ready.

Goals
- Provide a safe way to execute user-submitted code (notebooks or scripts) in an isolated environment.
- Support simple job submission from the API and a worker that executes jobs in containers.
- Keep the initial implementation minimal and easy to test.

What is included in this repo
- `backend/routes/jobs.py` — API endpoints to submit and view jobs.
- `backend/scripts/worker.py` — a worker scaffold that picks up job records and executes them.
- `backend/scripts/container_runner.py` — a small helper that runs a command inside a transient Docker container (development-only).

How it works (scaffold)
1. User submits a job via `/api/v1/jobs` with a payload that includes `command` or a reference to an uploaded artifact.
2. The API creates a `JobRecord` and enqueues the `run_job(job_id)` function (RQ if Redis available, otherwise left queued).
3. The worker (`backend/scripts/worker.py`) picks up the job and uses `container_runner.run_in_container(image, cmd, ...)` to run the command in a container.
4. Output and status are recorded in the `JobRecord`.

Security notes
- The included container runner is NOT production grade. It disables network (`--network none`) and limits memory, but more is needed:
  - Use a dedicated sandboxing technology (gVisor, Firecracker, Kata Containers) or run jobs in Kubernetes pods with strict resource limits.
  - Implement file system isolation, cgroups, seccomp, and user namespaces.
  - Validate and whitelist allowed commands or use an API that only supports predefined operations.

Next steps to make it production-ready
- Add an asynchronous worker pool (RQ/Redis or Kubernetes Jobs) and a retry/backoff policy.
- Implement artifact storage (S3) and allow only signed artifact references to be executed.
- Add job cancellation via container kill + cleanup.
- Implement audit logging and limits per user.
- Add e2e tests that exercise the runner and verify isolation.

Quick developer notes
- To test locally:
  - Ensure Docker is installed and running.
  - Submit a job via `POST /api/v1/jobs` with JSON `{ "language": "python", "payload": { "command": "python -c \"print(1+1)\"" } }`.
  - Run an RQ worker or call `backend/scripts/worker.run_job(job_id)` directly from a Python REPL inside the project (activating the virtualenv).

If you'd like, I can:
- Implement a small UI to submit jobs from the frontend.
- Add RQ worker docker-compose service to run background jobs.
- Harden the container runner with more isolation and logging.
