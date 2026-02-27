"""
Shared pytest fixtures for Compass test suite.

Unit tests (test_eligibility.py) need no fixtures — just the import.
API tests (test_api.py) use the `client` fixture which mocks AWS so no
real credentials are required in CI.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure compass/ root is on sys.path so `backend.*` imports resolve
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Environment — must be set before any backend module is imported
# ---------------------------------------------------------------------------
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("NOVA_ACT_ENABLED", "false")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(tmp_path):
    """
    Async HTTPX test client for the FastAPI app.

    - All boto3 calls are mocked so no AWS credentials are needed.
    - Uses a per-test SQLite file in a temp directory.
    - Nova Act is disabled via env var.
    - Manually initializes the orchestrator (httpx ASGITransport does not
      trigger FastAPI lifespan events, so we replicate what lifespan does).
    """
    db_file = str(tmp_path / "test_compass.db")
    os.environ["COMPASS_DB_PATH"] = db_file

    mock_boto3_client = MagicMock()
    # Make converse() return a minimal valid Bedrock response
    mock_boto3_client.converse.return_value = {
        "stopReason": "end_turn",
        "output": {"message": {"content": [{"text": "Hello! How can I help you today?"}]}},
        "usage": {"inputTokens": 10, "outputTokens": 20},
    }
    # converse_stream() returns an iterable stream
    mock_boto3_client.converse_stream.return_value = {
        "stream": [
            {"contentBlockStart": {"start": {"text": ""}}},
            {"contentBlockDelta": {"delta": {"text": "Hello!"}}},
            {"contentBlockStop": {}},
            {"messageStop": {"stopReason": "end_turn"}},
        ]
    }
    # invoke_model for embeddings — return a list of 1024 floats
    mock_boto3_client.invoke_model.return_value = {
        "body": MagicMock(read=MagicMock(return_value=b'{"embedding": [0.0] * 1024}'))
    }

    with patch("boto3.client", return_value=mock_boto3_client):
        import httpx
        import backend.main as main_module
        from backend.agents.orchestrator import CompassOrchestrator
        from backend.database import SessionStore
        from backend.main import app

        # httpx ASGITransport does not fire FastAPI lifespan events, so we
        # replicate what the lifespan would do: init DB + create orchestrator.
        store = SessionStore()
        await store.init_db()
        main_module.session_store = store
        main_module.orchestrator = CompassOrchestrator(store=store)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
