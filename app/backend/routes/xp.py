from flask import Blueprint, request, jsonify, Response
from backend.app import db
from backend.models import User, XPEvent
from backend.schemas import validate_award_payload, compute_new_level, next_level_threshold
from backend.auth import get_auth_user_id, require_auth_or_payload_user
from backend.rate_limiter import check_rate_limit
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import json
import time

xp_bp = Blueprint('xp', __name__)

@xp_bp.route('/api/v1/xp/award', methods=['POST'])
def award_xp():
    payload = request.get_json() or {}
    ok, err = validate_award_payload(payload)
    if not ok:
        return jsonify({'ok': False, 'error': err}), 400
    # prefer Authorization token, fallback to payload user_id for dev/test
    uid = get_auth_user_id()
    # require user id either from token or payload
    if uid is None and 'user_id' not in payload:
        return jsonify({'ok': False, 'error': 'user_id is required when no auth token provided'}), 400
    try:
        user_id = int(uid) if uid is not None else int(payload['user_id'])
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid user_id'}), 400

    # xp must be an integer > 0
    try:
        xp_amount = int(payload.get('xp', 0))
    except Exception:
        return jsonify({'ok': False, 'error': 'xp must be an integer'}), 400
    if xp_amount <= 0:
        return jsonify({'ok': False, 'error': 'xp must be a positive integer'}), 400

    source = payload.get('source')
    source_id = payload.get('source_id')
    metadata = payload.get('metadata')

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'ok': False, 'error': 'user not found'}), 404

    # rate limit (per-user if available, otherwise per-ip)
    rl_key = f"xp:{user.id}" if user else f"xp:anon:{request.remote_addr}"
    allowed, info = check_rate_limit(rl_key)
    if not allowed:
        return jsonify({'ok': False, 'error': 'rate_limited', 'retry_after': info.get('reset_seconds')}), 429

    # deduplicate via idempotency_key if provided
    idemp = payload.get('idempotency_key')
    if idemp:
        existing = db.session.query(XPEvent).filter_by(user_id=user.id, idempotency_key=idemp).first()
        if existing:
            return jsonify({
                'ok': True,
                'duplicate': True,
                'new_xp': user.xp_total,
                'new_level': user.level,
            })

    # deduplicate: if source+source_id provided, avoid creating duplicate XPEvent
    if source and source_id:
        existing = db.session.query(XPEvent).filter_by(user_id=user.id, source=source, source_id=source_id).first()
        if existing:
            return jsonify({
                'ok': True,
                'duplicate': True,
                'new_xp': user.xp_total,
                'new_level': user.level,
            })

    # transactionally update user totals and insert event
    try:
        # lock the user row for update to avoid race conditions (best-effort; sqlite may ignore FOR UPDATE)
        stmt = select(User).where(User.id == user.id).with_for_update()
        db.session.execute(stmt)
        event = XPEvent(user_id=user.id, amount=xp_amount, source=source, source_id=source_id, meta=metadata, idempotency_key=idemp)
        db.session.add(event)

        # update totals
        user.xp_total = (user.xp_total or 0) + xp_amount
        old_level = user.level or 1
        new_level = compute_new_level(user.xp_total)
        user.level = new_level

        db.session.commit()
    except IntegrityError:
        # unique constraint violation — treat as duplicate
        db.session.rollback()
        existing = None
        if idemp:
            existing = db.session.query(XPEvent).filter_by(user_id=user.id, idempotency_key=idemp).first()
        if not existing and source and source_id:
            existing = db.session.query(XPEvent).filter_by(user_id=user.id, source=source, source_id=source_id).first()
        if existing:
            return jsonify({
                'ok': True,
                'duplicate': True,
                'new_xp': user.xp_total,
                'new_level': user.level,
            })
        # otherwise re-raise
        raise

    leveled_up = new_level > old_level
    return jsonify({
        'ok': True,
        'new_xp': user.xp_total,
        'new_level': user.level,
        'leveled_up': leveled_up,
        'next_level_threshold': next_level_threshold(user.level),
    })

@xp_bp.route('/api/v1/leaderboard', methods=['GET'])
def leaderboard():
    limit = int(request.args.get('limit', 50))
    users = User.query.order_by(User.xp_total.desc()).limit(limit).all()
    rows = []
    rank = 1
    for u in users:
        rows.append({
            'rank': rank,
            'user_id': u.id,
            'display_name': u.display_name,
            'xp': u.xp_total,
            'level': u.level,
        })
        rank += 1
    return jsonify({'ok': True, 'rows': rows})


@xp_bp.route('/api/v1/leaderboard/stream')
def leaderboard_stream():
    def gen():
        last = None
        while True:
            users = User.query.order_by(User.xp_total.desc()).limit(50).all()
            rows = [{'rank': i+1, 'user_id': u.id, 'display_name': u.display_name, 'xp': u.xp_total, 'level': u.level} for i, u in enumerate(users)]
            payload = json.dumps({'rows': rows})
            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            time.sleep(2)
    return Response(gen(), mimetype='text/event-stream')
