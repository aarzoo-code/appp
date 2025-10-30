import time
import threading

import pytest

from backend.app import app, db
from backend.models import JobRecord


def test_worker_handles_cancel(test_client, monkeypatch):
    # ensure we have app context for DB operations in the main thread
    with app.app_context():
        # create a queued job with a dummy command
        job = JobRecord(payload={'command': 'sleep 1'}, status='queued')
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    # Prepare a simple container_runner mock
    class DummyRunner:
        def __init__(self):
            self.killed = False
            self._calls = 0
            import threading as _th
            self.started_event = _th.Event()

        def run_detached(self, image, cmd, memory=None):
            # notify test that the container was started
            try:
                self.started_event.set()
            except Exception:
                pass
            return 'dummy-cid'

        def is_running(self, cid):
            # Pretend the container is running for a while so the test can trigger cancel
            self._calls += 1
            return self._calls < 1000

        def kill_container(self, cid):
            self.killed = True

        def get_logs(self, cid):
            return 'dummy logs'

        def get_exit_code(self, cid):
            return 0

    runner = DummyRunner()
    # worker.py imported container_runner as a symbol; patch the name inside that module
    monkeypatch.setattr('backend.scripts.worker.container_runner', runner)
    # enable container runner branch for the worker
    monkeypatch.setenv('USE_CONTAINER_RUNNER', '1')
    monkeypatch.setenv('DOCKER_RUNNER_IMAGE', 'dummy-image')

    # import here to ensure the monkeypatch takes effect for the worker module
    from backend.scripts.worker import run_job

    # start the worker in a thread (it will create its own app context)
    def worker_target():
        with app.app_context():
            run_job(job_id)

    t = threading.Thread(target=worker_target)
    t.start()

    # wait for the worker to start the (mock) detached container
    started = runner.started_event.wait(timeout=1)
    assert started, 'worker did not start container'

    # mark job as cancelled from the test (use a new DB session via app context)
    with app.app_context():
        j = db.session.get(JobRecord, job_id)
        j.status = 'cancelled'
        db.session.commit()

    # wait for worker to finish
    t.join(timeout=5)
    assert not t.is_alive()

    # verify job status and output contain cancellation marker and logs
    with app.app_context():
        j = db.session.get(JobRecord, job_id)
        assert j.status == 'cancelled'
        assert '[cancelled]' in (j.output or '')
        assert 'dummy logs' in (j.output or '')
