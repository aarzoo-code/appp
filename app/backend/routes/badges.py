from flask import Blueprint, request, jsonify
from backend.app import db
from backend.models import Badge, UserBadge, User
from backend.auth import get_auth_user_id

badges_bp = Blueprint('badges', __name__)


@badges_bp.route('/api/v1/badges', methods=['GET'])
def list_badges():
    b = Badge.query.all()
    rows = [{'id': x.id, 'code': x.code, 'name': x.name, 'description': x.description, 'icon': x.icon} for x in b]
    return jsonify({'ok': True, 'badges': rows})


@badges_bp.route('/api/v1/users/<int:user_id>/badges', methods=['POST'])
def award_badge(user_id):
    data = request.get_json() or {}
    badge_code = data.get('code')
    if not badge_code:
        return jsonify({'ok': False, 'error': 'badge code required'}), 400

    # if Authorization header present, use that user and ensure it matches path user_id
    token_uid = get_auth_user_id()
    if token_uid is not None and int(token_uid) != int(user_id):
        return jsonify({'ok': False, 'error': 'user mismatch with token'}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'ok': False, 'error': 'user not found'}), 404
    badge = Badge.query.filter_by(code=badge_code).first()
    if not badge:
        return jsonify({'ok': False, 'error': 'badge not found'}), 404
    # avoid duplicates
    existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
    if existing:
        return jsonify({'ok': True, 'message': 'already awarded'})
    ub = UserBadge(user_id=user.id, badge_id=badge.id)
    db.session.add(ub)
    db.session.commit()
    return jsonify({'ok': True, 'awarded': {'user_id': user.id, 'badge_id': badge.id}}), 201
