import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from tests.conftest import make_db_mock


# ── unit: _gql ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gql_http_error():
    from api.buffer import _gql
    mock_response = MagicMock(status_code=401, text='Unauthorized')
    with patch('api.buffer.httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        with pytest.raises(HTTPException) as exc:
            await _gql('query { channels { id } }')
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_gql_graphql_error():
    from api.buffer import _gql
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {'errors': [{'message': 'Unauthorized'}]}
    with patch('api.buffer.httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        with pytest.raises(HTTPException) as exc:
            await _gql('query { channels { id } }')
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_gql_success():
    from api.buffer import _gql
    mock_response = MagicMock(status_code=200)
    mock_response.json.return_value = {'data': {'channels': []}}
    with patch('api.buffer.httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        result = await _gql('query { channels { id } }')
    assert result == {'channels': []}


# ── unit: _get_channels ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_channels_returns_linkedin_and_twitter():
    from api.buffer import _get_channels
    with patch('api.buffer._gql', new=AsyncMock(return_value={
        'channels': [
            {'id': 'li1', 'service': 'linkedin', 'name': 'Penjy LinkedIn'},
            {'id': 'tw1', 'service': 'twitter',  'name': 'Penjy Twitter'},
        ]
    })):
        channels = await _get_channels()
    assert channels == {'linkedin': 'li1', 'twitter': 'tw1'}


@pytest.mark.asyncio
async def test_get_channels_takes_first_of_each_service():
    from api.buffer import _get_channels
    with patch('api.buffer._gql', new=AsyncMock(return_value={
        'channels': [
            {'id': 'li1', 'service': 'linkedin', 'name': 'First'},
            {'id': 'li2', 'service': 'linkedin', 'name': 'Second'},
        ]
    })):
        channels = await _get_channels()
    assert channels['linkedin'] == 'li1'
    assert 'twitter' not in channels


@pytest.mark.asyncio
async def test_get_channels_empty():
    from api.buffer import _get_channels
    with patch('api.buffer._gql', new=AsyncMock(return_value={'channels': []})):
        channels = await _get_channels()
    assert channels == {}


# ── unit: schedule_draft ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_schedule_draft_not_found():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[])
    with patch('api.buffer.get_db', return_value=db):
        with pytest.raises(HTTPException) as exc:
            await schedule_draft(999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_schedule_draft_wrong_status():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'scheduled',
                                                   'linkedin_draft': 'L', 'x_draft': 'X'}])
    with patch('api.buffer.get_db', return_value=db):
        with pytest.raises(HTTPException) as exc:
            await schedule_draft(1)
    assert exc.value.status_code == 400
    assert 'scheduled' in exc.value.detail


@pytest.mark.asyncio
async def test_schedule_draft_no_matching_channels():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'L', 'x_draft': 'X'}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={})):
        with pytest.raises(HTTPException) as exc:
            await schedule_draft(1)
    assert exc.value.status_code == 400
    assert 'No matching' in exc.value.detail


@pytest.mark.asyncio
async def test_schedule_draft_linkedin_only():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'LinkedIn text',
                                                   'x_draft': None}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'post': {'id': 'buf1', 'text': 'L'}}})):
        result = await schedule_draft(1)
    assert 'linkedin' in result['scheduled_to']
    assert 'twitter' not in result['scheduled_to']


@pytest.mark.asyncio
async def test_schedule_draft_both_platforms():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'LinkedIn text',
                                                   'x_draft': 'X text'}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1', 'twitter': 'ch2'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'post': {'id': 'buf1', 'text': 'post'}}})):
        result = await schedule_draft(1)
    assert set(result['scheduled_to']) == {'linkedin', 'twitter'}
    assert result['draft_id'] == 1


@pytest.mark.asyncio
async def test_schedule_draft_buffer_mutation_error():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'L', 'x_draft': None}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'message': 'Channel not found'}})):
        with pytest.raises(HTTPException) as exc:
            await schedule_draft(1)
    assert exc.value.status_code == 502
    assert 'LinkedIn post failed' in exc.value.detail


@pytest.mark.asyncio
async def test_schedule_draft_saves_as_draft():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'L', 'x_draft': None}])
    gql_mock = AsyncMock(return_value={'createPost': {'post': {'id': 'buf1', 'text': 'L'}}})
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1'})), \
         patch('api.buffer._gql', gql_mock):
        await schedule_draft(1, save_as_draft=True)

    # Verify saveToDraft=True was passed
    call_vars = gql_mock.call_args[0][1]
    assert call_vars['saveToDraft'] is True


@pytest.mark.asyncio
async def test_schedule_draft_updates_db_status():
    from api.buffer import schedule_draft
    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'L', 'x_draft': None}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'post': {'id': 'buf1', 'text': 'L'}}})):
        await schedule_draft(1)

    # Verify update was called with status=scheduled
    update_calls = [str(c) for c in chain.update.call_args_list]
    assert any('scheduled' in c for c in update_calls)


# ── integration: POST /buffer/schedule/{id} ──────────────────────────────────

def test_buffer_schedule_endpoint():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 1, 'status': 'pending',
                                                   'linkedin_draft': 'L', 'x_draft': None}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'post': {'id': 'buf1', 'text': 'L'}}})):
        r = client.post('/buffer/schedule/1')

    assert r.status_code == 200
    assert 'linkedin' in r.json()['scheduled_to']


def test_buffer_save_as_draft_endpoint():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)

    db, chain = make_db_mock()
    chain.execute.return_value = MagicMock(data=[{'id': 2, 'status': 'pending',
                                                   'linkedin_draft': 'L', 'x_draft': None}])
    with patch('api.buffer.get_db', return_value=db), \
         patch('api.buffer._get_channels', new=AsyncMock(return_value={'linkedin': 'ch1'})), \
         patch('api.buffer._gql', new=AsyncMock(return_value={'createPost': {'post': {'id': 'buf2', 'text': 'L'}}})):
        r = client.post('/buffer/draft/2')

    assert r.status_code == 200
