import hashlib
import hmac
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from tests.conftest import make_db_mock


# ── unit: _verify_signature ───────────────────────────────────────────────────

def test_verify_signature_valid():
    from api.webhooks import _verify_signature
    secret = 'mysecret'
    body = b'{"action": "push"}'
    sig = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': secret}):
        assert _verify_signature(body, sig) is True


def test_verify_signature_invalid():
    from api.webhooks import _verify_signature
    with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'mysecret'}):
        assert _verify_signature(b'body', 'sha256=wrongsig') is False


def test_verify_signature_missing_header():
    from api.webhooks import _verify_signature
    with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'mysecret'}):
        assert _verify_signature(b'body', None) is False


# ── unit: _importance ─────────────────────────────────────────────────────────

def test_importance_high():
    from api.webhooks import _importance
    assert _importance(70) == 'high'
    assert _importance(90) == 'high'


def test_importance_medium():
    from api.webhooks import _importance
    assert _importance(20) == 'medium'
    assert _importance(69) == 'medium'


def test_importance_low():
    from api.webhooks import _importance
    assert _importance(0) == 'low'
    assert _importance(19) == 'low'


# ── unit: _score_event ────────────────────────────────────────────────────────

def test_score_push_main():
    from api.webhooks import _score_event
    payload = {'ref': 'refs/heads/main', 'commits': [{}, {}]}
    etype, pts = _score_event('push', payload)
    assert etype == 'push_main'
    assert pts == 40  # 30 + 5*2


def test_score_push_master():
    from api.webhooks import _score_event
    payload = {'ref': 'refs/heads/master', 'commits': [{}]}
    etype, pts = _score_event('push', payload)
    assert etype == 'push_main'
    assert pts == 35  # 30 + 5*1


def test_score_push_branch():
    from api.webhooks import _score_event
    payload = {'ref': 'refs/heads/feature/auth', 'commits': [{}, {}, {}]}
    etype, pts = _score_event('push', payload)
    assert etype == 'push_branch'
    assert pts == 16  # 10 + 2*3


def test_score_push_zero_commits():
    from api.webhooks import _score_event
    payload = {'ref': 'refs/heads/main', 'commits': []}
    etype, pts = _score_event('push', payload)
    assert etype == 'push_main'
    assert pts == 30  # 30 + 5*0


def test_score_release_published():
    from api.webhooks import _score_event
    etype, pts = _score_event('release', {'action': 'published'})
    assert etype == 'release'
    assert pts == 90


def test_score_release_not_published():
    from api.webhooks import _score_event
    etype, pts = _score_event('release', {'action': 'created'})
    assert pts == 0


def test_score_pr_merged():
    from api.webhooks import _score_event
    payload = {'action': 'closed', 'pull_request': {'merged': True, 'title': 'Fix auth'}}
    etype, pts = _score_event('pull_request', payload)
    assert etype == 'pr_merged'
    assert pts == 70


def test_score_pr_closed_not_merged():
    from api.webhooks import _score_event
    payload = {'action': 'closed', 'pull_request': {'merged': False}}
    etype, pts = _score_event('pull_request', payload)
    assert pts == 0


def test_score_pr_opened():
    from api.webhooks import _score_event
    etype, pts = _score_event('pull_request', {'action': 'opened'})
    assert etype == 'pr_opened'
    assert pts == 20


def test_score_issue_closed():
    from api.webhooks import _score_event
    etype, pts = _score_event('issues', {'action': 'closed'})
    assert etype == 'issue_closed'
    assert pts == 15


def test_score_issue_opened():
    from api.webhooks import _score_event
    etype, pts = _score_event('issues', {'action': 'opened'})
    assert pts == 0


def test_score_fork():
    from api.webhooks import _score_event
    etype, pts = _score_event('fork', {})
    assert etype == 'fork'
    assert pts == 10


def test_score_star_created():
    from api.webhooks import _score_event
    etype, pts = _score_event('star', {'action': 'created'})
    assert etype == 'star'
    assert pts == 5


def test_score_star_deleted():
    from api.webhooks import _score_event
    etype, pts = _score_event('star', {'action': 'deleted'})
    assert pts == 0


def test_score_repo_created():
    from api.webhooks import _score_event
    etype, pts = _score_event('repository', {'action': 'created'})
    assert etype == 'repo_created'
    assert pts == 25


def test_score_repo_publicized():
    from api.webhooks import _score_event
    etype, pts = _score_event('repository', {'action': 'publicized'})
    assert etype == 'repo_publicized'
    assert pts == 40


def test_score_unknown_event():
    from api.webhooks import _score_event
    etype, pts = _score_event('ping', {})
    assert pts == 0


# ── integration: POST /webhooks/github ───────────────────────────────────────

@pytest.fixture
def client():
    from api.main import app
    return TestClient(app, raise_server_exceptions=False)


def _make_sig(body: bytes, secret: str = 'testsecret') -> str:
    return 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_invalid_signature(client):
    body = json.dumps({'ref': 'refs/heads/main', 'commits': [], 'repository': {'full_name': 'penjy/test'}}).encode()
    r = client.post('/webhooks/github', content=body, headers={
        'x-github-event': 'push',
        'x-hub-signature-256': 'sha256=badsig',
    })
    assert r.status_code == 401


def test_webhook_ignored_event(client):
    body = json.dumps({'action': 'ping', 'repository': {'full_name': 'penjy/test'}}).encode()
    with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'testsecret'}):
        r = client.post('/webhooks/github', content=body, headers={
            'x-github-event': 'ping',
            'x-hub-signature-256': _make_sig(body),
        })
    assert r.status_code == 200
    assert r.json()['status'] == 'ignored'


def test_webhook_push_main_writes_db(client):
    payload = {'ref': 'refs/heads/main', 'commits': [{}], 'repository': {'full_name': 'penjy/specnest'}}
    body = json.dumps(payload).encode()
    db_mock, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1}])

    with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'testsecret'}), \
         patch('api.webhooks.get_db', return_value=db_mock):
        r = client.post('/webhooks/github', content=body, headers={
            'x-github-event': 'push',
            'x-hub-signature-256': _make_sig(body),
        })

    assert r.status_code == 200
    data = r.json()
    assert data['event'] == 'push_main'
    assert data['points'] == 35


def test_webhook_high_importance_triggers_draft(client):
    payload = {'action': 'published', 'release': {'name': 'v1.0'}, 'repository': {'full_name': 'penjy/specnest'}}
    body = json.dumps(payload).encode()
    db_mock, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 42}])

    with patch.dict('os.environ', {'GITHUB_WEBHOOK_SECRET': 'testsecret'}), \
         patch('api.webhooks.get_db', return_value=db_mock), \
         patch('api.content.generate_draft', new=AsyncMock()) as mock_draft:
        r = client.post('/webhooks/github', content=body, headers={
            'x-github-event': 'release',
            'x-hub-signature-256': _make_sig(body),
        })

    assert r.status_code == 200
    assert r.json()['points'] == 90
