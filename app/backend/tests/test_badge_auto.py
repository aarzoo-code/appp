import pytest
from backend.app import app, db


def test_auto_award_first_100_xp(test_client):
    # create user
    rv = test_client.post('/api/v1/users', json={'display_name': 'AutoBadgeUser'})
    assert rv.status_code == 201
    uid = rv.get_json()['user']['id']

    # award 100 xp via endpoint
    r = test_client.post('/api/v1/xp/award', json={'user_id': uid, 'xp': 100, 'source': 'test'})
    assert r.status_code == 200
    d = r.get_json()
    assert d.get('ok') is True

    # verify badge present
    r2 = test_client.get(f'/api/v1/users/{uid}/badges')
    assert r2.status_code == 200
    badges = r2.get_json().get('badges')
    codes = [b['code'] for b in badges]
    assert 'first_100_xp' in codes


def test_auto_award_5_day_streak(test_client):
    # create user
    rv = test_client.post('/api/v1/users', json={'display_name': 'StreakUser'})
    uid = rv.get_json()['user']['id']

    # create streak directly
    with app.app_context():
        from backend.models import Streak
        s = Streak(user_id=uid, current_streak=5)
        db.session.add(s)
        db.session.commit()

    # trigger xp award to invoke badge evaluation
    r = test_client.post('/api/v1/xp/award', json={'user_id': uid, 'xp': 10, 'source': 'test'})
    assert r.status_code == 200

    # verify badge present
    r2 = test_client.get(f'/api/v1/users/{uid}/badges')
    assert r2.status_code == 200
    badges = r2.get_json().get('badges')
    codes = [b['code'] for b in badges]
    assert '5_day_streak' in codes
