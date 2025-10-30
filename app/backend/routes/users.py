from flask import Blueprint, jsonify, request
from backend.app import db
from backend.models import User, XPEvent, UserBadge, Badge, Streak
from backend.schemas import compute_new_level, next_level_threshold
from flask import Blueprint, jsonify, request
from backend.auth import get_auth_user_id

users_bp = Blueprint('users', __name__)


@users_bp.route('/api/v1/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    name = data.get('display_name') or data.get('name') or 'Anonymous'
    email = data.get('email')
    u = User(display_name=name, email=email)
    db.session.add(u)
    db.session.commit()
    return jsonify({'ok': True, 'user': u.to_dict()}), 201


@users_bp.route('/api/v1/users/<int:user_id>/stats', methods=['GET'])
def user_stats(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({'ok': False, 'error': 'user not found'}), 404
    events = XPEvent.query.filter_by(user_id=u.id).order_by(XPEvent.created_at.desc()).limit(10).all()
    recent = [{'id': e.id, 'amount': e.amount, 'source': e.source, 'created_at': e.created_at.isoformat()} for e in events]

    # include earned badges
    user_badges = UserBadge.query.filter_by(user_id=u.id).join(Badge, UserBadge.badge_id == Badge.id).all()
    badges = []
    # Note: join above returns UserBadge objects; fetch badge records
    for ub in UserBadge.query.filter_by(user_id=u.id).all():
        b = db.session.get(Badge, ub.badge_id)
        if b:
            badges.append({'id': b.id, 'code': b.code, 'name': b.name, 'earned_at': ub.earned_at.isoformat()})

    return jsonify({'ok': True, 'user': u.to_dict(), 'recent_events': recent, 'badges': badges})


@users_bp.route('/api/v1/users/<int:user_id>/badges', methods=['GET'])
def list_user_badges(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({'ok': False, 'error': 'user not found'}), 404
    ubs = UserBadge.query.filter_by(user_id=u.id).all()
    rows = []
    for ub in ubs:
        b = db.session.get(Badge, ub.badge_id)
        if b:
            rows.append({'id': b.id, 'code': b.code, 'name': b.name, 'description': b.description, 'earned_at': ub.earned_at.isoformat()})
    return jsonify({'ok': True, 'badges': rows})


@users_bp.route('/api/v1/me/progress', methods=['GET'])
def me_progress():
    """Return current authenticated user's progress: xp, level, streak, recent xp events and badges."""
    uid = get_auth_user_id()
    if uid is None:
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401

    u = db.session.get(User, int(uid))
    if not u:
        return jsonify({'ok': False, 'error': 'user not found'}), 404

    # streak info (if present)
    streak = Streak.query.filter_by(user_id=u.id).first()
    streak_info = {}
    if streak:
        streak_info = {
            'current_streak': streak.current_streak,
            'last_checkin_date': streak.last_checkin_date.isoformat() if streak.last_checkin_date else None,
        }

    # recent xp events
    events = XPEvent.query.filter_by(user_id=u.id).order_by(XPEvent.created_at.desc()).limit(10).all()
    recent = [{'id': e.id, 'amount': e.amount, 'source': e.source, 'created_at': e.created_at.isoformat()} for e in events]

    # earned badges
    ubs = UserBadge.query.filter_by(user_id=u.id).all()
    badges = []
    for ub in ubs:
        b = db.session.get(Badge, ub.badge_id)
        if b:
            badges.append({'id': b.id, 'code': b.code, 'name': b.name, 'earned_at': ub.earned_at.isoformat()})

    # include level/progression info using existing XP math
    current_xp = getattr(u, 'xp_total', 0) or 0
    current_level = getattr(u, 'level', 1) or 1
    next_threshold = next_level_threshold(current_level)
    xp_to_next = max(0, next_threshold - current_xp)
    # percent progress toward next level (0-100)
    prev_threshold = next_level_threshold(current_level - 1) if current_level > 1 else 0
    denom = max(1, next_threshold - prev_threshold)
    progress_pct = int(((current_xp - prev_threshold) / denom) * 100) if denom else 0

    return jsonify({
        'ok': True,
        'user': u.to_dict(),
        'streak': streak_info,
        'recent_events': recent,
        'badges': badges,
        'xp': current_xp,
        'level': current_level,
        'xp_to_next': xp_to_next,
        'next_level_threshold': next_threshold,
        'level_progress_percent': progress_pct,
    })



@users_bp.route('/api/v1/me/checkin', methods=['POST'])
def me_checkin():
    """Daily check-in: increments streak once per day and awards a small XP bonus.

    Returns duplicate if already checked in today.
    """
    uid = get_auth_user_id()
    if uid is None:
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401

    u = db.session.get(User, int(uid))
    if not u:
        return jsonify({'ok': False, 'error': 'user not found'}), 404

    from datetime import date

    today = date.today()
    streak = Streak.query.filter_by(user_id=u.id).first()
    if not streak:
        streak = Streak(user_id=u.id, current_streak=0, last_checkin_date=None)
        db.session.add(streak)

    if streak.last_checkin_date == today:
        return jsonify({'ok': True, 'duplicate': True, 'message': 'already checked in today', 'current_streak': streak.current_streak}), 200

    # increment streak
    streak.current_streak = (streak.current_streak or 0) + 1
    streak.last_checkin_date = today

    # award small XP for checkin
    xp_award = 10
    from backend.schemas import compute_new_level

    from backend.models import XPEvent
    ev = XPEvent(user_id=u.id, amount=xp_award, source='daily_checkin', source_id=today.isoformat())
    db.session.add(ev)

    u.xp_total = (u.xp_total or 0) + xp_award
    old_level = u.level or 1
    new_level = compute_new_level(u.xp_total)
    u.level = new_level

    db.session.commit()

    leveled_up = new_level > old_level
    # Evaluate badges and return awarded badge codes
    awarded = []
    try:
        from backend.gamification import evaluate_badges_for_user
        awarded = evaluate_badges_for_user(db.session, u) or []
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({'ok': True, 'new_xp': u.xp_total, 'new_level': u.level, 'leveled_up': leveled_up, 'current_streak': streak.current_streak, 'awarded_badges': awarded}), 200
