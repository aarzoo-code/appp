"""Worker utility for executing enqueued jobs.

This script defines `run_job(job_id)` which the RQ worker can call.
It will update JobRecord status and write output.

Note: this is a minimal example. Real execution should sandbox code in containers.
"""
import subprocess
import shlex
from datetime import datetime
from backend.app import db
from backend.models import JobRecord
import os
from backend.scripts import container_runner


def run_job(job_id: int):
    # run job identified by job_id; this function is intended to be enqueued by RQ
    session = db.session
    job = session.get(JobRecord, job_id)
    if not job:
        return 'job not found'
    job.status = 'running'
    job.started_at = datetime.utcnow()
    session.commit()

    # For safety in this scaffold, do not execute arbitrary code.
    # If payload contains {'command': '...'}, we could run a safe subset.
    try:
        payload = job.payload or {}
        cmd = payload.get('command') if isinstance(payload, dict) else None
        if not cmd:
            job.output = 'no command provided; execution disabled in scaffold'
            job.status = 'finished'
            job.finished_at = datetime.utcnow()
            session.commit()
            return job.output

        # If configured, run inside a container runner image for better isolation.
        image = os.getenv('DOCKER_RUNNER_IMAGE')
        if os.getenv('USE_CONTAINER_RUNNER', '0') in ('1', 'true', 'True') and image:
            rc, out = container_runner.run_in_container(image, cmd, timeout= int(os.getenv('JOB_RUN_TIMEOUT', '30')),
                                                      memory=os.getenv('JOB_RUN_MEMORY', '256m'))
            job.output = out
            job.status = 'finished' if rc == 0 else 'failed'
            job.finished_at = datetime.utcnow()
            session.commit()
            return out

        # Fallback to simple local execution (unsafe for untrusted code)
        args = shlex.split(cmd)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        out = proc.stdout.decode('utf-8', errors='replace')
        job.output = out
        job.status = 'finished'
        job.finished_at = datetime.utcnow()
        session.commit()
        return out
    except Exception as e:
        job.output = f'error during execution: {e}'
        job.status = 'failed'
        job.finished_at = datetime.utcnow()
        session.commit()
        return job.output
