import json
import pytest
from backend.app import app, db


def test_list_and_cancel_jobs(test_client):
    # create user and token
    rv = test_client.post('/api/v1/auth/signup', json={'username': 'jobsuser', 'password': 'pw', 'display_name': 'JobsUser'})
    assert rv.status_code == 201
    token = rv.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # submit a job
    r1 = test_client.post('/api/v1/jobs', json={'language': 'python', 'payload': {'code': 'print(1)'}}, headers=headers)
    assert r1.status_code == 201
    job_id = r1.get_json()['job_id']

    # list jobs should include the created job
    rl = test_client.get('/api/v1/jobs', headers=headers)
    assert rl.status_code == 200
    jobs = rl.get_json().get('jobs', [])
    assert any(j['id'] == job_id for j in jobs)

    # get job details
    rg = test_client.get(f'/api/v1/jobs/{job_id}', headers=headers)
    assert rg.status_code == 200
    assert rg.get_json()['job']['id'] == job_id

    # cancel job
    rc = test_client.post(f'/api/v1/jobs/{job_id}/cancel', headers=headers)
    assert rc.status_code == 200
    data = rc.get_json()
    assert data.get('ok') is True or data.get('cancelled') is True

    # verify job is marked cancelled
    rg2 = test_client.get(f'/api/v1/jobs/{job_id}', headers=headers)
    assert rg2.status_code == 200
    assert rg2.get_json()['job']['status'] == 'cancelled'
