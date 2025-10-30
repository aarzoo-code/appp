import os
import jwt
from datetime import datetime, timedelta, timezone
from flask import request, jsonify

SECRET = os.getenv('SECRET_KEY', 'dev-secret')
ALGORITHM = 'HS256'


def create_token(user_id: int, expires_minutes: int = 60 * 24 * 7) -> str:
    payload = {
        'sub': str(user_id),
        # use timezone-aware datetimes to avoid deprecation warnings
        'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        data = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return int(data.get('sub'))
    except Exception:
        return None


def get_auth_user_id():
    auth = request.headers.get('Authorization')
    if not auth:
        return None
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
    else:
        token = auth
    return decode_token(token)


def require_auth_or_payload_user(payload_user_key: str = 'user_id'):
    """Helper to extract user id from Authorization header or fallback to request json payload."""
    def inner():
        uid = get_auth_user_id()
        if uid is not None:
            return uid
        # fallback to payload
        try:
            data = request.get_json() or {}
            return int(data.get(payload_user_key)) if data.get(payload_user_key) is not None else None
        except Exception:
            return None
    return inner
