from flask import Blueprint, request, jsonify, current_app, abort
from backend.app import db
from backend.models import JobRecord, User
from backend.auth import get_auth_user_id
from backend.rate_limiter import check_rate_limit
from time import time
import os
import json
try:
    import redis
    _Redis = redis.Redis
except Exception:
    _Redis = None

# simple in-memory quota store for jobs when Redis is not available: {user_id: [timestamps...]}
_job_quota_store = {}

jobs_bp = Blueprint('jobs', __name__)


def _get_redis_conn():
    """Return a Redis connection from REDIS_URL or None."""
    redis_url = current_app.config.get('REDIS_URL')
    if not redis_url or _Redis is None:
        return None
    try:
        return _Redis.from_url(redis_url)
    except Exception:
        return None


@jobs_bp.route('/api/v1/jobs', methods=['POST'])
def submit_job():
    data = request.get_json() or {}
    uid = get_auth_user_id()
    # require authentication for job submission
    if uid is None:
        return jsonify({'ok': False, 'error': 'authentication required'}), 401
    user_id = int(uid)
    language = data.get('language', 'python')
    payload = data.get('payload')

    # basic validation
    if language != 'python':
        return jsonify({'ok': False, 'error': 'only python supported in this MVP'}), 400

    # payload size limit (configurable)
    max_payload = int(current_app.config.get('JOB_MAX_PAYLOAD_BYTES', 20000))
    try:
        payload_s = json.dumps(payload) if not isinstance(payload, str) else payload
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid payload'}), 400

    if len(payload_s.encode('utf-8')) > max_payload:
        return jsonify({'ok': False, 'error': 'payload_too_large'}), 400

    job = JobRecord(user_id=user_id, language=language, payload=payload_s, status='queued')

    # enforce simple per-user job quota (configurable)
    quota = int(current_app.config.get('JOB_QUOTA_PER_MINUTE', 10))
    window = int(current_app.config.get('JOB_QUOTA_WINDOW_SECONDS', 60))
    now = int(time())

    conn = _get_redis_conn()
    if conn:
        try:
            # use fixed window keyed by window start timestamp
            window_start = now - (now % window)
            key = f"job_quota:{user_id}:{window_start}"
            val = conn.incr(key)
            if val == 1:
                conn.expire(key, window)
            if int(val) > quota:
                ttl = conn.ttl(key) or window
                return jsonify({'ok': False, 'error': 'job_rate_limited', 'retry_after': int(ttl)}), 429
        except Exception:
            # fallback to in-memory if Redis not reachable
            conn = None

    if not conn:
        # in-memory fallback (per-process only)
        entries = _job_quota_store.get(user_id, [])
        entries = [t for t in entries if t > now - window]
        if len(entries) >= quota:
            return jsonify({'ok': False, 'error': 'job_rate_limited', 'retry_after': entries[0] + window - now}), 429
        entries.append(now)
        _job_quota_store[user_id] = entries

    db.session.add(job)
    db.session.commit()

    # Try to enqueue to Redis RQ if configured; otherwise leave as queued for manual worker
    conn = _get_redis_conn()
    if conn:
        try:
            from rq import Queue
            from redis import Redis
            # import worker function lazily
            from backend.scripts.worker import run_job
            q = Queue('default', connection=conn)
            q.enqueue(run_job, job.id)
            job.status = 'enqueued'
            db.session.commit()
        except Exception as e:
            # leave job as queued but record the enqueue failure for observability
            current_app.logger.exception('failed to enqueue job')
            job.output = f'failed to enqueue: {str(e)}'
            db.session.commit()

    return jsonify({'ok': True, 'job_id': job.id, 'status': job.status}), 201


@jobs_bp.route('/api/v1/jobs', methods=['GET'])
def list_jobs():
    """List jobs for the authenticated user (simple pagination)."""
    uid = get_auth_user_id()
    if uid is None:
        return jsonify({'ok': False, 'error': 'authentication required'}), 401
    user_id = int(uid)
    limit = min(int(request.args.get('limit', 50)), 200)
    offset = int(request.args.get('offset', 0))
    qs = db.session.query(JobRecord).filter_by(user_id=user_id).order_by(JobRecord.created_at.desc())
    items = qs.offset(offset).limit(limit).all()
    return jsonify({'ok': True, 'jobs': [
        {'id': j.id, 'status': j.status, 'created_at': j.created_at.isoformat() if j.created_at else None}
        for j in items
    ]})


@jobs_bp.route('/api/v1/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = db.session.get(JobRecord, job_id)
    if not job:
        return jsonify({'ok': False, 'error': 'job not found'}), 404
    uid = get_auth_user_id()
    if uid is None or int(uid) != job.user_id:
        return jsonify({'ok': False, 'error': 'not authorized'}), 403
    return jsonify({'ok': True, 'job': {
        'id': job.id,
        'user_id': job.user_id,
        'language': job.language,
        'status': job.status,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'finished_at': job.finished_at.isoformat() if job.finished_at else None,
        'output': job.output,
    }})


@jobs_bp.route('/api/v1/jobs/<int:job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Attempt to cancel a queued/enqueued job. This is a best-effort operation."""
    job = db.session.get(JobRecord, job_id)
    if not job:
        return jsonify({'ok': False, 'error': 'job not found'}), 404
    uid = get_auth_user_id()
    if uid is None or int(uid) != job.user_id:
        return jsonify({'ok': False, 'error': 'not authorized'}), 403

    if job.status in ('finished', 'failed', 'cancelled'):
        return jsonify({'ok': False, 'error': 'cannot_cancel', 'status': job.status}), 400

    # try to remove from RQ queue if present
    conn = _get_redis_conn()
    removed = False
    if conn:
        try:
            from rq import Queue
            q = Queue('default', connection=conn)
            # find jobs with meta or arg matching our job id; best-effort
            for queued in q.jobs:
                try:
                    if queued.args and queued.args[0] == job.id:
                        queued.cancel()
                        removed = True
                except Exception:
                    continue
        except Exception:
            current_app.logger.exception('failed to query RQ for cancel')

    job.status = 'cancelled'
    job.finished_at = job.finished_at or None
    job.output = (job.output or '') + '\n[cancelled by user]'
    db.session.commit()
    return jsonify({'ok': True, 'cancelled': True, 'removed_from_queue': removed})
