"""Worker utility for executing enqueued jobs.

This script defines `run_job(job_id)` which the RQ worker can call.
It will update JobRecord status and write output.

Note: this is a minimal example. Real execution should sandbox code in containers.
"""
import subprocess
import shlex
from datetime import datetime, timezone
from backend.app import db
from backend.models import JobRecord
import os
from backend.scripts import container_runner
import time


def run_job(job_id: int):
    # run job identified by job_id; this function is intended to be enqueued by RQ
    session = db.session
    job = session.get(JobRecord, job_id)
    if not job:
        return 'job not found'
    job.status = 'running'
    job.started_at = datetime.now(timezone.utc)
    session.commit()

    # For safety in this scaffold, do not execute arbitrary code.
    # If payload contains {'command': '...'}, we could run a safe subset.
    try:
        payload = job.payload or {}
        cmd = payload.get('command') if isinstance(payload, dict) else None
        if not cmd:
            job.output = 'no command provided; execution disabled in scaffold'
            job.status = 'finished'
            job.finished_at = datetime.now(timezone.utc)
            session.commit()
            return job.output

        # If configured, run inside a container runner image for better isolation.
        image = os.getenv('DOCKER_RUNNER_IMAGE')
        if os.getenv('USE_CONTAINER_RUNNER', '0') in ('1', 'true', 'True') and image:
            # start container detached and record container id to allow cancellation
            try:
                cid = container_runner.run_detached(image, cmd, memory=os.getenv('JOB_RUN_MEMORY', '256m'))
            except Exception as e:
                job.output = f'failed to start container: {e}'
                job.status = 'failed'
                job.finished_at = datetime.now(timezone.utc)
                session.commit()
                return job.output

            job.runner_container_id = cid
            session.commit()

            timeout = int(os.getenv('JOB_RUN_TIMEOUT', '30'))
            poll_interval = 1
            elapsed = 0

            # poll until container exits or job is cancelled
            while True:
                # refresh job from DB
                session.expire(job)
                session.refresh(job)
                if job.status == 'cancelled':
                    # attempt to kill container
                    container_runner.kill_container(cid)
                    job.output = (job.output or '') + '\n[cancelled]'
                    job.status = 'cancelled'
                    job.finished_at = datetime.now(timezone.utc)
                    session.commit()
                    # try to collect logs for debugging
                    try:
                        logs = container_runner.get_logs(cid)
                        job.output = (job.output or '') + '\n' + logs
                        session.commit()
                    except Exception:
                        pass
                    return job.output

                # check if container still running
                if not container_runner.is_running(cid):
                    exit_code = container_runner.get_exit_code(cid)
                    logs = container_runner.get_logs(cid)
                    job.output = (job.output or '') + '\n' + (logs or '')
                    job.status = 'finished' if exit_code == 0 else 'failed'
                    job.finished_at = datetime.now(timezone.utc)
                    session.commit()
                    return job.output

                time.sleep(poll_interval)
                elapsed += poll_interval
                if elapsed >= timeout:
                    # timeout: kill container
                    container_runner.kill_container(cid)
                    logs = container_runner.get_logs(cid)
                    job.output = (job.output or '') + '\n' + (logs or '')
                    job.status = 'failed'
                    job.finished_at = datetime.now(timezone.utc)
                    session.commit()
                    return job.output

        # Fallback to simple local execution (unsafe for untrusted code)
        args = shlex.split(cmd)
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=int(os.getenv('LOCAL_RUN_TIMEOUT', '30')),
        )
        out = proc.stdout.decode('utf-8', errors='replace')
        job.output = out
        job.status = 'finished'
        job.finished_at = datetime.now(timezone.utc)
        session.commit()
        return out
    except Exception as e:
        # Ensure we set finished_at and persist the failure
        try:
            job.output = f'error during execution: {e}'
            job.status = 'failed'
            job.finished_at = datetime.now(timezone.utc)
            session.commit()
        except Exception:
            # If committing fails, there's not much we can do in the worker scaffold
            pass
        return str(e)
