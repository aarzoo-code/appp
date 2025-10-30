import os
import sys
import json
import tempfile

# ensure repo root on path when running tests directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.app import app, db
from backend.models import User


def test_ping(test_client):
    rv = test_client.get('/api/v1/ping')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get('ok') is True


def test_create_and_get_user_stats(test_client):
    # create a new user
    rv = test_client.post('/api/v1/users', json={'display_name': 'NewUser', 'email': 'new@example.com'})
    assert rv.status_code == 201
    user = rv.get_json().get('user')
    assert user and 'id' in user

    uid = user['id']
    # get stats
    rv2 = test_client.get(f'/api/v1/users/{uid}/stats')
    assert rv2.status_code == 200
    data = rv2.get_json()
    assert data.get('user')['id'] == uid


def test_award_xp_and_leaderboard(test_client):
    # create user A
    rv = test_client.post('/api/v1/users', json={'display_name': 'A'})
    ua = rv.get_json()['user']
    rv = test_client.post('/api/v1/users', json={'display_name': 'B'})
    ub = rv.get_json()['user']

    # award xp to A
    rv = test_client.post('/api/v1/xp/award', json={'user_id': ua['id'], 'xp': 150, 'source': 'test'})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get('ok') is True
    assert 'new_xp' in data

    # leaderboard should include users
    rv2 = test_client.get('/api/v1/leaderboard')
    assert rv2.status_code == 200
    rows = rv2.get_json().get('rows')
    assert isinstance(rows, list)


def test_badge_listing_and_award(test_client):
    # list badges (none initially)
    rv = test_client.get('/api/v1/badges')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'badges' in data

    # create a badge directly in DB and award it via endpoint
    with app.app_context():
        from backend.models import Badge
        b = Badge(code='test_badge', name='Test Badge')
        db.session.add(b)
        db.session.commit()
        bid = b.id

    # create user
    rv = test_client.post('/api/v1/users', json={'display_name': 'BadgeUser'})
    uid = rv.get_json()['user']['id']

    rv2 = test_client.post(f'/api/v1/users/{uid}/badges', json={'code': 'test_badge'})
    assert rv2.status_code in (200,201)
    data2 = rv2.get_json()
    assert data2.get('ok') is True

    rv3 = test_client.get(f'/api/v1/users/{uid}/badges')
    assert rv3.status_code == 200
    badges = rv3.get_json().get('badges')
    assert isinstance(badges, list)
    assert any(b['code'] == 'test_badge' for b in badges)


def test_award_xp_idempotency(test_client):
    # create user
    rv = test_client.post('/api/v1/users', json={'display_name': 'IdemUser'})
    assert rv.status_code == 201
    uid = rv.get_json()['user']['id']

    # award XP with a stable source+source_id
    payload = {'user_id': uid, 'xp': 100, 'source': 'challenge', 'source_id': 'challenge-42'}
    r1 = test_client.post('/api/v1/xp/award', json=payload)
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1.get('ok') is True
    first_xp = d1.get('new_xp')
    assert first_xp == 100

    # send the same award again -- should be idempotent
    r2 = test_client.post('/api/v1/xp/award', json=payload)
    assert r2.status_code == 200
    d2 = r2.get_json()
    # should indicate duplicate and not increase xp
    assert d2.get('ok') is True
    assert d2.get('duplicate') is True
    assert d2.get('new_xp') == first_xp


def test_award_xp_with_idempotency_key(test_client):
    # create user
    rv = test_client.post('/api/v1/users', json={'display_name': 'IdemKeyUser'})
    assert rv.status_code == 201
    uid = rv.get_json()['user']['id']

    payload = {'user_id': uid, 'xp': 50, 'idempotency_key': 'key-1234'}
    r1 = test_client.post('/api/v1/xp/award', json=payload)
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1.get('ok') is True
    assert d1.get('new_xp') == 50

    # repeat with same idempotency key
    r2 = test_client.post('/api/v1/xp/award', json=payload)
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert d2.get('duplicate') is True
    assert d2.get('new_xp') == 50


def test_signup_and_login(test_client):
    # signup
    rv = test_client.post('/api/v1/auth/signup', json={'username': 'u1', 'password': 'pass123', 'display_name': 'U One'})
    assert rv.status_code == 201
    data = rv.get_json()
    assert data.get('ok') is True
    assert 'token' in data

    # login
    rv2 = test_client.post('/api/v1/auth/login', json={'username': 'u1', 'password': 'pass123'})
    assert rv2.status_code == 200
    d2 = rv2.get_json()
    assert d2.get('ok') is True
    assert 'token' in d2


def test_award_xp_rate_limit(test_client):
    # configure a low rate limit for the test
    test_client.application.config['XP_RATE_LIMIT'] = '2:60'

    rv = test_client.post('/api/v1/users', json={'display_name': 'RateUser'})
    uid = rv.get_json()['user']['id']

    payload = {'user_id': uid, 'xp': 10}
    r1 = test_client.post('/api/v1/xp/award', json=payload)
    assert r1.status_code == 200
    r2 = test_client.post('/api/v1/xp/award', json=payload)
    assert r2.status_code == 200
    # third call should be rate limited
    r3 = test_client.post('/api/v1/xp/award', json=payload)
    assert r3.status_code == 429


def test_jobs_require_auth_and_quota(test_client):
    # create user and get token
    rv = test_client.post('/api/v1/auth/signup', json={'username': 'jobuser', 'password': 'pw', 'display_name': 'JobUser'})
    token = rv.get_json()['token']

    headers = {'Authorization': f'Bearer {token}'}
    # submit up to quota
    app = test_client.application
    app.config['JOB_QUOTA_PER_MINUTE'] = 2
    app.config['JOB_QUOTA_WINDOW_SECONDS'] = 60

    r1 = test_client.post('/api/v1/jobs', json={'language': 'python', 'payload': {}}, headers=headers)
    assert r1.status_code == 201
    r2 = test_client.post('/api/v1/jobs', json={'language': 'python', 'payload': {}}, headers=headers)
    assert r2.status_code == 201
    # third should be rate limited
    r3 = test_client.post('/api/v1/jobs', json={'language': 'python', 'payload': {}}, headers=headers)
    assert r3.status_code == 429

    # unauthenticated submission should be rejected
    r4 = test_client.post('/api/v1/jobs', json={'language': 'python', 'payload': {}})
    assert r4.status_code == 401


def test_me_progress_endpoint(test_client):
    # signup a new user and use returned token to query /api/v1/me/progress
    rv = test_client.post('/api/v1/auth/signup', json={'username': 'meuser', 'password': 'pw', 'display_name': 'MeUser'})
    assert rv.status_code == 201
    token = rv.get_json().get('token')
    assert token

    headers = {'Authorization': f'Bearer {token}'}
    r = test_client.get('/api/v1/me/progress', headers=headers)
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is True
    assert 'user' in data
    assert 'streak' in data
    assert 'recent_events' in data
    assert 'badges' in data


def test_me_checkin_endpoint(test_client):
    # signup a new user and get token
    rv = test_client.post('/api/v1/auth/signup', json={'username': 'checkinuser', 'password': 'pw', 'display_name': 'CheckIn'})
    assert rv.status_code == 201
    token = rv.get_json().get('token')
    headers = {'Authorization': f'Bearer {token}'}

    # first checkin should award XP and increment streak
    r1 = test_client.post('/api/v1/me/checkin', headers=headers)
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1.get('ok') is True
    assert 'new_xp' in d1
    assert 'current_streak' in d1

    # second checkin same day should be duplicate and not award more XP
    r2 = test_client.post('/api/v1/me/checkin', headers=headers)
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert d2.get('duplicate') is True
