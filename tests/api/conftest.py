"""API test configuration — async client + memory reset."""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.infrastructure.database.repositories.memory.state import MemoryState

os.environ["DATA_MODE"] = "memory"


@pytest.fixture
def memory_state():
    """Fresh memory state for each test."""
    state = MemoryState()
    state.clear()
    yield state
    state.clear()


@pytest_asyncio.fixture
async def client(memory_state):
    """Async HTTP client for API tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
