import sys
import os
from unittest.mock import MagicMock, AsyncMock
import pytest

# Stub env vars before any module-level os.environ reads
os.environ.setdefault('GROQ_API_KEY', 'test-key')
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'test-key')
os.environ.setdefault('BUFFER_ACCESS_TOKEN', 'test-token')
os.environ.setdefault('GITHUB_WEBHOOK_SECRET', 'testsecret')

# Stub out heavy dependencies before any app module is imported
for mod in ('supabase', 'groq', 'telegram', 'telegram.ext', 'uvicorn'):
    sys.modules.setdefault(mod, MagicMock())

# supabase.create_client must be callable and return a mock
sys.modules['supabase'].create_client = MagicMock(return_value=MagicMock())


def make_db_mock():
    """Returns a mock Supabase client with chainable .table().select()... pattern."""
    db = MagicMock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.upsert.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.neq.return_value = chain
    chain.gte.return_value = chain
    chain.in_.return_value = chain
    chain.not_ = chain          # attribute, not return_value
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    db.table.return_value = chain
    return db, chain


def make_project(overrides=None):
    base = {
        'id': 'SpecNest',
        'tier': 'A',
        'status': 'active',
        'revenue_potential': 'direct',
        'completion': 75,
        'last_activity': '2026-04-29',
        'deadline': '2026-05-15',
        'priority_boost': 15,
        'description': 'Computer marketplace',
        'next_milestone': 'Fix auth bug',
        'github_repo': 'penjy/specnest',
    }
    if overrides:
        base.update(overrides)
    return base
