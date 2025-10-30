from flask import Blueprint, request, jsonify, current_app
from backend.app import db
from backend.models import Badge, BadgeRule, User
from backend.auth import get_auth_user_id
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


def require_admin():
    # admin gate with two modes:
    # 1. prefer DB-driven admin: if request has Authorization bearer token, decode user id and check User.is_admin
    # 2. fallback to legacy X-Admin-Token env var for CI/backwards compatibility
    def _inner():
        try:
            uid = get_auth_user_id()
            if uid is not None:
                user = db.session.get(User, int(uid))
                if user and getattr(user, 'is_admin', False):
                    return True
        except Exception:
            # ignore and fall back to token header
            pass

        token = request.headers.get('X-Admin-Token')
        if token and token == os.getenv('ADMIN_TOKEN'):
            return True
        return False

    return _inner


@admin_bp.route('/badges', methods=['GET'])
def list_badges():
    badges = Badge.query.all()
    rows = [{'id': b.id, 'code': b.code, 'name': b.name, 'description': b.description} for b in badges]
    return jsonify({'ok': True, 'badges': rows})


@admin_bp.route('/badges', methods=['POST'])
def create_badge():
    gate = require_admin()
    if not gate():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    data = request.get_json() or {}
    code = data.get('code')
    name = data.get('name')
    if not code or not name:
        return jsonify({'ok': False, 'error': 'code and name required'}), 400
    b = Badge(code=code, name=name, description=data.get('description'))
    db.session.add(b)
    db.session.commit()
    return jsonify({'ok': True, 'badge': {'id': b.id, 'code': b.code}}), 201


@admin_bp.route('/rules', methods=['GET'])
def list_rules():
    gate = require_admin()
    if not gate():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    rules = BadgeRule.query.all()
    rows = [{'id': r.id, 'code': r.code, 'rule_type': r.rule_type, 'params': r.params} for r in rules]
    return jsonify({'ok': True, 'rules': rows})


@admin_bp.route('/rules', methods=['POST'])
def create_rule():
    gate = require_admin()
    if not gate():
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    data = request.get_json() or {}
    code = data.get('code')
    rule_type = data.get('rule_type')
    params = data.get('params')
    if not code or not rule_type:
        return jsonify({'ok': False, 'error': 'code and rule_type required'}), 400
    r = BadgeRule(code=code, rule_type=rule_type, params=params)
    db.session.add(r)
    db.session.commit()
    return jsonify({'ok': True, 'rule': {'id': r.id, 'code': r.code}}), 201
