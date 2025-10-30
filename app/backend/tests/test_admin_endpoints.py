import os
from backend.app import app, db
from backend.models import User
from backend.auth import create_token


def test_admin_create_and_list_badge(test_client):
    # ensure ADMIN_TOKEN set
    os.environ['ADMIN_TOKEN'] = 'admintoken'
    headers = {'X-Admin-Token': 'admintoken'}

    r = test_client.post('/api/v1/admin/badges', json={'code': 'admin_test', 'name': 'Admin Test'}, headers=headers)
    assert r.status_code == 201
    d = r.get_json()
    assert d.get('ok') is True

    r2 = test_client.get('/api/v1/admin/badges', headers=headers)
    assert r2.status_code == 200
    assert any(b['code'] == 'admin_test' for b in r2.get_json().get('badges', []))


def test_admin_create_with_db_admin_user(test_client):
    """Verify DB-driven admin via JWT works: create a user, mark is_admin, and call admin endpoint with Bearer token."""
    # create admin user
    with app.app_context():
        u = User(display_name='AdminUser', email='admin@example.com')
        u.is_admin = True
        db.session.add(u)
        db.session.commit()
        uid = u.id

    token = create_token(uid)
    headers = {'Authorization': f'Bearer {token}'}

    r = test_client.post('/api/v1/admin/badges', json={'code': 'db_admin_test', 'name': 'DB Admin Test'}, headers=headers)
    assert r.status_code == 201
    d = r.get_json()
    assert d.get('ok') is True

    r2 = test_client.get('/api/v1/admin/badges', headers=headers)
    assert r2.status_code == 200
    assert any(b['code'] == 'db_admin_test' for b in r2.get_json().get('badges', []))
