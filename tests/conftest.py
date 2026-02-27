"""
Shared pytest fixtures for Compass test suite.

Unit tests (test_eligibility.py) need no fixtures — just the import.
API tests (test_api.py) use the `client` fixture which mocks AWS so no
real credentials are required in CI.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

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

@pytest_asyncio.fixture
async def client(tmp_path):
    """
    Async HTTPX test client for the FastAPI app.

    - All boto3 calls are mocked so no AWS credentials are needed.
    - Uses a per-test SQLite file in a temp directory.
    - Nova Act is disabled via env var.
    """
    # Point DB at a temp file for this test
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
    # embed_text — return a list of 1024 floats
    mock_boto3_client.invoke_model.return_value = {
        "body": MagicMock(read=MagicMock(return_value=b'{"embedding": [0.0] * 1024}'))
    }

    with patch("boto3.client", return_value=mock_boto3_client):
        import httpx
        from backend.main import app

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
