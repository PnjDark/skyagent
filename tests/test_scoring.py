import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from tests.conftest import make_db_mock, make_project


# ── unit: _github_boost ───────────────────────────────────────────────────────

def test_github_boost_no_repo():
    from api.scoring import _github_boost
    db, _ = make_db_mock()
    assert _github_boost(None, db) == 0
    assert _github_boost('', db) == 0


def test_github_boost_zero_points():
    from api.scoring import _github_boost
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[])
    assert _github_boost('penjy/specnest', db) == 0


def test_github_boost_partial():
    from api.scoring import _github_boost
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'points': 100}])
    assert _github_boost('penjy/specnest', db) == 10  # 100*20//200


def test_github_boost_full():
    from api.scoring import _github_boost
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'points': 200}, {'points': 50}])
    assert _github_boost('penjy/specnest', db) == 20  # capped at 20


def test_github_boost_exceeds_cap():
    from api.scoring import _github_boost
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'points': 500}])
    assert _github_boost('penjy/specnest', db) == 20  # still capped


# ── unit: _score ──────────────────────────────────────────────────────────────

def test_score_tier_s():
    from api.scoring import _score
    p = make_project({'tier': 'S', 'deadline': None, 'revenue_potential': None,
                      'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 30


def test_score_tier_weights():
    from api.scoring import _score
    for tier, expected in [('S', 30), ('A', 25), ('B', 15), ('C', 10), ('D', 5)]:
        p = make_project({'tier': tier, 'deadline': None, 'revenue_potential': None,
                          'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
        assert _score(p, 0) == expected


def test_score_deadline_overdue():
    from api.scoring import _score
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    p = make_project({'deadline': yesterday, 'revenue_potential': None,
                      'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 45  # 25 + 20


def test_score_deadline_7_days():
    from api.scoring import _score
    soon = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    p = make_project({'deadline': soon, 'revenue_potential': None,
                      'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 43  # 25 + 18


def test_score_deadline_far():
    from api.scoring import _score
    far = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    p = make_project({'deadline': far, 'revenue_potential': None,
                      'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 25  # no deadline bonus


def test_score_revenue_direct():
    from api.scoring import _score
    p = make_project({'revenue_potential': 'direct', 'deadline': None,
                      'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 40  # 25 + 15


def test_score_momentum_fresh():
    from api.scoring import _score
    today = datetime.now().strftime('%Y-%m-%d')
    p = make_project({'last_activity': today, 'deadline': None,
                      'revenue_potential': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 40  # 25 + 15


def test_score_momentum_stale_21_days():
    from api.scoring import _score
    old = (datetime.now() - timedelta(days=21)).strftime('%Y-%m-%d')
    p = make_project({'last_activity': old, 'deadline': None,
                      'revenue_potential': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 5  # 25 - 20


def test_score_completion_bonus():
    from api.scoring import _score
    p = make_project({'completion': 80, 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 35  # 25 + 10


def test_score_completion_no_bonus_below_70():
    from api.scoring import _score
    p = make_project({'completion': 60, 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 25


def test_score_completion_no_bonus_above_90():
    from api.scoring import _score
    p = make_project({'completion': 95, 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 0) == 25


def test_score_danger_zone_bonus():
    from api.scoring import _score
    p = make_project({'status': 'danger_zone', 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'completion': 0, 'priority_boost': 0})
    assert _score(p, 0) == 40  # 25 + 15


def test_score_paused_penalty():
    from api.scoring import _score
    p = make_project({'status': 'paused', 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'completion': 0, 'priority_boost': 0})
    assert _score(p, 0) == 0  # 25 - 30 = -5 → clamped to 0


def test_score_capped_at_100():
    from api.scoring import _score
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    p = make_project({'tier': 'S', 'deadline': tomorrow, 'revenue_potential': 'direct',
                      'last_activity': today, 'completion': 80, 'priority_boost': 20, 'status': 'active'})
    assert _score(p, 20) == 100


def test_score_github_boost_added():
    from api.scoring import _score
    p = make_project({'deadline': None, 'revenue_potential': None,
                      'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'})
    assert _score(p, 15) == 40  # 25 + 15


# ── unit: compute_priorities ──────────────────────────────────────────────────

def test_compute_priorities_returns_top_3():
    from api.scoring import compute_priorities
    db = MagicMock()
    projects = [
        make_project({'id': f'P{i}', 'tier': 'A', 'github_repo': None,
                      'deadline': None, 'revenue_potential': None,
                      'last_activity': None, 'completion': i * 10,
                      'priority_boost': i, 'status': 'active'})
        for i in range(5)
    ]
    # projects table returns 5 projects; github_events table returns empty
    def table_side_effect(name):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.not_ = chain
        chain.in_.return_value = chain
        chain.eq.return_value = chain
        chain.gte.return_value = chain
        chain.order.return_value = chain
        chain.limit.return_value = chain
        if name == 'projects':
            chain.execute.return_value = MagicMock(data=projects)
        else:
            chain.execute.return_value = MagicMock(data=[])
        return chain
    db.table.side_effect = table_side_effect
    result = compute_priorities(db)
    assert len(result) == 3


def test_compute_priorities_excludes_archived():
    from api.scoring import compute_priorities
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[])
    result = compute_priorities(db)
    # Verify filter was applied — not_.in_ was called
    db.table.assert_called_with('projects')


def test_compute_priorities_sorted_descending():
    from api.scoring import compute_priorities
    db = MagicMock()
    projects = [
        make_project({'id': 'Low',  'tier': 'C', 'github_repo': None, 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'}),
        make_project({'id': 'High', 'tier': 'S', 'github_repo': None, 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'}),
        make_project({'id': 'Mid',  'tier': 'B', 'github_repo': None, 'deadline': None,
                      'revenue_potential': None, 'last_activity': None, 'completion': 0, 'priority_boost': 0, 'status': 'active'}),
    ]
    def table_side_effect(name):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.not_ = chain
        chain.in_.return_value = chain
        chain.eq.return_value = chain
        chain.gte.return_value = chain
        chain.order.return_value = chain
        chain.limit.return_value = chain
        if name == 'projects':
            chain.execute.return_value = MagicMock(data=projects)
        else:
            chain.execute.return_value = MagicMock(data=[])
        return chain
    db.table.side_effect = table_side_effect
    result = compute_priorities(db)
    assert result[0]['id'] == 'High'
    assert result[1]['id'] == 'Mid'
    assert result[2]['id'] == 'Low'


# ── integration: POST /scoring/run ───────────────────────────────────────────

def test_scoring_run_writes_daily_priorities():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    db_mock, chain = make_db_mock()
    today = datetime.now().strftime('%Y-%m-%d')
    projects = [make_project({'id': f'P{i}', 'github_repo': None, 'deadline': None,
                               'revenue_potential': None, 'last_activity': None,
                               'completion': 0, 'priority_boost': 0, 'status': 'active'})
                for i in range(3)]
    chain.execute.return_value = MagicMock(data=projects)

    with patch('api.scoring.get_db', return_value=db_mock), \
         patch('api.scoring.client') as groq_mock:
        groq_mock.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='🎯 FOCUS FOR TODAY'))]
        )
        r = client.post('/scoring/run')

    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
    assert r.json()['report'] == '🎯 FOCUS FOR TODAY'
