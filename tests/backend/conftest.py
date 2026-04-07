"""Backend test configuration — memory mode enforcement."""

import os
import pytest

os.environ["DATA_MODE"] = "memory"


@pytest.fixture(autouse=True)
def enforce_memory_mode():
    """Ensure all backend tests run in memory mode."""
    assert os.environ.get("DATA_MODE") == "memory", "Tests must run with DATA_MODE=memory"
