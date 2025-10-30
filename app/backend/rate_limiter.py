from time import time
from threading import Lock
from flask import current_app

# Try to use Redis if available; otherwise fallback to simple in-memory windowed counter.
try:
    import redis
except Exception:
    redis = None

_store = {}
_lock = Lock()


def _parse_config(cfg: str):
    # expects "max:seconds"
    try:
        parts = cfg.split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 1000, 60


def _redis_check(key: str):
    cfg = current_app.config.get('XP_RATE_LIMIT', '1000:60')
    max_calls, window = _parse_config(cfg)
    now = int(time())
    window_start = now - (now % window)
    rkey = f"rl:{key}:{window_start}"
    r = None
    try:
        r = redis.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
        val = r.incr(rkey)
        if val == 1:
            # set expiry to window seconds
            r.expire(rkey, window)
        remaining = max_calls - int(val)
        allowed = int(val) <= max_calls
        reset_seconds = window_start + window - now
        return allowed, {'remaining': max(0, remaining), 'reset_seconds': reset_seconds}
    except Exception:
        # Redis not available or failed; fallback to in-memory
        return None


def _memory_check(key: str):
    cfg = current_app.config.get('XP_RATE_LIMIT', '1000:60')
    max_calls, window = _parse_config(cfg)
    now = int(time())
    window_start = now - (now % window)
    with _lock:
        entry = _store.get(key)
        if not entry or entry.get('window') != window_start:
            # reset
            _store[key] = {'count': 0, 'window': window_start}
            entry = _store[key]
        if entry['count'] < max_calls:
            entry['count'] += 1
            remaining = max_calls - entry['count']
            return True, {'remaining': remaining, 'reset_seconds': window_start + window - now}
        else:
            return False, {'remaining': 0, 'reset_seconds': window_start + window - now}


def check_rate_limit(key: str) -> tuple[bool, dict]:
    """Return (allowed: bool, info dict)
    info contains: remaining, reset_seconds
    """
    if redis is not None:
        res = _redis_check(key)
        if res is not None:
            return res
    # fallback
    return _memory_check(key)
