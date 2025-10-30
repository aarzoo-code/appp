from flask import Blueprint, request, jsonify, current_app, redirect
from backend.auth import create_token
from backend.app import db
from backend.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/v1/auth/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    username = data.get('username')
    display_name = data.get('display_name') or username
    password = data.get('password')
    email = data.get('email')
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    # check uniqueness (avoid NULL matching where email is None)
    existing = db.session.query(User).filter(User.username == username).first()
    if existing:
        return jsonify({'ok': False, 'error': 'username already exists'}), 400
    if email:
        if db.session.query(User).filter(User.email == email).first():
            return jsonify({'ok': False, 'error': 'email already exists'}), 400
    pw_hash = generate_password_hash(password)
    user = User(username=username, display_name=display_name or username, email=email, password_hash=pw_hash)
    db.session.add(user)
    db.session.commit()
    token = create_token(user.id)
    return jsonify({'ok': True, 'token': token, 'user': user.to_dict()}), 201


@auth_bp.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'ok': False, 'error': 'username and password required'}), 400
    user = db.session.query(User).filter_by(username=username).first()
    if not user or not user.password_hash:
        return jsonify({'ok': False, 'error': 'invalid credentials'}), 401
    if not check_password_hash(user.password_hash, password):
        return jsonify({'ok': False, 'error': 'invalid credentials'}), 401
    token = create_token(user.id)
    return jsonify({'ok': True, 'token': token, 'user': user.to_dict()})


@auth_bp.route('/api/v1/auth/github', methods=['GET'])
def github_oauth():
    # scaffold: redirect to GitHub OAuth authorize URL if client id configured
    client_id = os.getenv('GITHUB_CLIENT_ID')
    redirect_uri = os.getenv('GITHUB_REDIRECT_URI')
    if not client_id or not redirect_uri:
        return jsonify({'ok': False, 'error': 'GitHub OAuth not configured'}), 501
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'read:user user:email',
    }
    url = 'https://github.com/login/oauth/authorize'
    return redirect(f"{url}?client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user user:email")


@auth_bp.route('/api/v1/auth/github/callback', methods=['GET'])
def github_callback():
    # exchange code for token and find/create user
    code = request.args.get('code')
    client_id = os.getenv('GITHUB_CLIENT_ID')
    client_secret = os.getenv('GITHUB_CLIENT_SECRET')
    if not client_id or not client_secret or not code:
        return jsonify({'ok': False, 'error': 'GitHub OAuth misconfigured or missing code'}), 400
    token_url = 'https://github.com/login/oauth/access_token'
    headers = {'Accept': 'application/json'}
    data = {'client_id': client_id, 'client_secret': client_secret, 'code': code}
    r = requests.post(token_url, data=data, headers=headers)
    if r.status_code != 200:
        return jsonify({'ok': False, 'error': 'failed to exchange code'}), 400
    token_data = r.json()
    access_token = token_data.get('access_token')
    if not access_token:
        return jsonify({'ok': False, 'error': 'no access token from GitHub'}), 400
    # fetch user info
    user_info = requests.get('https://api.github.com/user', headers={'Authorization': f'token {access_token}'}).json()
    github_id = str(user_info.get('id'))
    display_name = user_info.get('name') or user_info.get('login')
    email = user_info.get('email')
    user = db.session.query(User).filter_by(github_id=github_id).first()
    if not user:
        # create new user
        user = User(display_name=display_name or github_id, email=email, github_id=github_id)
        db.session.add(user)
        db.session.commit()
    token = create_token(user.id)
    return jsonify({'ok': True, 'token': token, 'user': user.to_dict()})


# retain dev-login for local dev but gate it behind a config flag
@auth_bp.route('/api/v1/auth/dev-login', methods=['POST'])
def dev_login():
    if not current_app.config.get('ALLOW_DEV_LOGIN', True):
        return jsonify({'ok': False, 'error': 'dev-login disabled'}), 403
    data = request.get_json() or {}
    uid = data.get('user_id')
    try:
        uid = int(uid)
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid user_id'}), 400
    token = create_token(uid)
    return jsonify({'ok': True, 'token': token})
