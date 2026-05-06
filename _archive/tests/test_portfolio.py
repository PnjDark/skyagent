from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tests.conftest import make_db_mock, make_project


def test_portfolio_feed_returns_public_shape():
    from api.main import app

    client = TestClient(app)
    db, chain = make_db_mock()
    chain.execute.side_effect = [
        MagicMock(data=[
            make_project(),
            make_project({'id': 'OldThing', 'status': 'archived'}),
        ]),
        MagicMock(data=[
            {
                'id': 1,
                'project_id': 'SpecNest',
                'event_type': 'release',
                'summary': 'Released v1.0',
                'date': '2026-05-01',
                'type': 'launch',
            }
        ]),
    ]

    with patch('api.portfolio.get_db', return_value=db):
        response = client.get('/portfolio/feed')

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {'generated_at', 'projects', 'recent_activity'}
    assert len(body['projects']) == 1
    assert body['projects'][0]['id'] == 'SpecNest'
    assert body['projects'][0]['github_url'] == 'https://github.com/penjy/specnest'
    assert body['recent_activity'][0]['summary'] == 'Released v1.0'


def test_portfolio_feed_limit_is_bounded():
    from api.main import app

    client = TestClient(app)
    response = client.get('/portfolio/feed?limit=101')

    assert response.status_code == 422
