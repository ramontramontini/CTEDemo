"""Root test configuration — memory state cleanup."""

import pytest
from src.infrastructure.database.repositories.memory.state import MemoryState


@pytest.fixture(autouse=True, scope="session")
def clean_memory_state():
    """Reset memory state before test session."""
    state = MemoryState()
    state.clear()
    yield
    state.clear()
