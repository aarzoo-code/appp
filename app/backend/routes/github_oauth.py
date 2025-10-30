from flask import Blueprint, redirect, request, jsonify, url_for
import os
import requests
from backend.app import db
from backend.models import User
from backend.auth import create_token
from datetime import datetime, timezone


github_bp = Blueprint('github_oauth', __name__, url_prefix='/api/v1/integrations/github')


@github_bp.route('/start', methods=['GET'])
def start_github_oauth():
    """Return a URL to start GitHub OAuth flow."""
    client_id = os.getenv('GITHUB_OAUTH_CLIENT_ID', 'your-client-id')
    redirect_uri = request.args.get('redirect_uri') or url_for('github_oauth.github_callback', _external=True)
    state = request.args.get('state', 'state')
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&state={state}"
    return jsonify({'ok': True, 'auth_url': url})


@github_bp.route('/callback', methods=['GET', 'POST'])
def github_callback():
    """Exchange code for an access token, fetch GitHub user, and create/link a local user.

    Returns a JWT token and user info in JSON. In production you'd set a secure cookie
    and validate `state` and redirect back to the frontend.
    """
    code = request.args.get('code') or request.form.get('code')
    if not code:
        return jsonify({'ok': False, 'error': 'missing code'}), 400

    client_id = os.getenv('GITHUB_OAUTH_CLIENT_ID')
    client_secret = os.getenv('GITHUB_OAUTH_CLIENT_SECRET')
    if not client_id or not client_secret:
        return jsonify({'ok': False, 'error': 'OAuth client not configured'}), 500

    # Exchange code for access token
    token_url = 'https://github.com/login/oauth/access_token'
    headers = {'Accept': 'application/json'}
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
    }
    try:
        r = requests.post(token_url, headers=headers, data=data, timeout=10)
        r.raise_for_status()
        token_json = r.json()
        access_token = token_json.get('access_token')
        if not access_token:
            return jsonify({'ok': False, 'error': 'no access token from provider', 'details': token_json}), 400

        # Fetch GitHub user
        user_resp = requests.get('https://api.github.com/user', headers={'Authorization': f'token {access_token}'}, timeout=10)
        user_resp.raise_for_status()
        gh = user_resp.json()
        gh_id = str(gh.get('id'))
        gh_login = gh.get('login')
        gh_email = gh.get('email')

        # create or update local user
        session = db.session
        user = session.query(User).filter_by(github_id=gh_id).one_or_none()
        if not user:
            # create a new user - display_name prefers GitHub name or login
            display_name = gh.get('name') or gh_login or f'github-{gh_id}'
            user = User(github_id=gh_id, username=gh_login, display_name=display_name, email=gh_email)
            session.add(user)
            session.commit()
        else:
            # optionally update email/display_name if missing
            changed = False
            if not user.display_name and gh.get('name'):
                user.display_name = gh.get('name')
                changed = True
            if not user.email and gh_email:
                user.email = gh_email
                changed = True
            if changed:
                session.commit()

        token = create_token(user.id)

        return jsonify({'ok': True, 'token': token, 'user': user.to_dict()})
    except requests.RequestException as exc:
        return jsonify({'ok': False, 'error': 'oauth request failed', 'details': str(exc)}), 502
    except Exception as exc:  # catch DB/other errors
        return jsonify({'ok': False, 'error': 'server error', 'details': str(exc)}), 500
