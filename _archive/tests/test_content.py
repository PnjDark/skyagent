import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from tests.conftest import make_db_mock, make_project


# ── unit: generate_draft ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_draft_skips_non_draft_events():
    from api.content import generate_draft
    db, _ = make_db_mock()
    with patch('api.content.get_db', return_value=db):
        await generate_draft(1, 'penjy/specnest', 'push_main', {})
    db.table.assert_not_called()


@pytest.mark.asyncio
async def test_generate_draft_release_writes_db():
    from api.content import generate_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[make_project()])

    groq_response = json.dumps({
        'linkedin': 'LinkedIn post text',
        'x': 'X post text',
        'portfolio_update': 'Updated description',
    })

    with patch('api.content.get_db', return_value=db), \
         patch('api.content.client') as groq_mock:
        groq_mock.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=groq_response))]
        )
        await generate_draft(1, 'penjy/specnest', 'release',
                             {'release': {'name': 'v1.0'}})

    # content_drafts insert was called
    insert_calls = [str(c) for c in db.table.call_args_list]
    assert any('content_drafts' in c for c in insert_calls)


@pytest.mark.asyncio
async def test_generate_draft_unknown_project_uses_repo_as_fallback():
    from api.content import generate_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[])  # no project found

    groq_response = json.dumps({'linkedin': 'L', 'x': 'X', 'portfolio_update': 'P'})

    with patch('api.content.get_db', return_value=db), \
         patch('api.content.client') as groq_mock:
        groq_mock.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=groq_response))]
        )
        # Should not raise — falls back to repo name as project id
        await generate_draft(1, 'penjy/unknown-repo', 'release', {'release': {'name': 'v1.0'}})


@pytest.mark.asyncio
async def test_generate_draft_all_trigger_events():
    from api.content import generate_draft, DRAFT_EVENTS
    assert DRAFT_EVENTS == {'release', 'pr_merged', 'repo_publicized', 'repo_created'}

    for event in DRAFT_EVENTS:
        db, chain = make_db_mock()
        chain.execute.return_value = MagicMock(data=[make_project()])
        groq_response = json.dumps({'linkedin': 'L', 'x': 'X', 'portfolio_update': 'P'})

        with patch('api.content.get_db', return_value=db), \
             patch('api.content.client') as groq_mock:
            groq_mock.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=groq_response))]
            )
            await generate_draft(1, 'penjy/specnest', event, {
                'release': {'name': 'v1'},
                'pull_request': {'title': 'Fix'},
            })
        db.table.assert_called()


@pytest.mark.asyncio
async def test_generate_draft_portfolio_feed_written():
    from api.content import generate_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[make_project()])
    groq_response = json.dumps({'linkedin': 'L', 'x': 'X', 'portfolio_update': 'P'})

    with patch('api.content.get_db', return_value=db), \
         patch('api.content.client') as groq_mock:
        groq_mock.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=groq_response))]
        )
        await generate_draft(1, 'penjy/specnest', 'release', {'release': {'name': 'v1.0'}})

    tables_written = [call.args[0] for call in db.table.call_args_list]
    assert 'portfolio_feed' in tables_written


# ── integration: GET /content/drafts ─────────────────────────────────────────

def test_list_drafts_returns_pending():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[
        {'id': 1, 'project_id': 'SpecNest', 'linkedin_draft': 'L', 'x_draft': 'X', 'status': 'pending'}
    ])

    with patch('api.content.get_db', return_value=db):
        r = client.get('/content/drafts')

    assert r.status_code == 200
    assert len(r.json()) == 1


# ── integration: POST /content/drafts/{id}/approve ───────────────────────────

@pytest.mark.asyncio
async def test_approve_draft_calls_buffer():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{
        'id': 1, 'status': 'pending',
        'linkedin_draft': 'LinkedIn text',
        'x_draft': 'X text',
    }])

    with patch('api.content.get_db', return_value=db), \
         patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1', 'twitter': 'ch2'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'post': {'id': 'buf123', 'text': 'test'}}})):
        r = client.post('/content/drafts/1/approve')

    assert r.status_code == 200
    assert r.json()['status'] == 'scheduled'


# ── integration: POST /content/drafts/{id}/reject ────────────────────────────

def test_reject_draft():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[])

    with patch('api.content.get_db', return_value=db):
        r = client.post('/content/drafts/1/reject')

    assert r.status_code == 200
    assert r.json()['status'] == 'rejected'
