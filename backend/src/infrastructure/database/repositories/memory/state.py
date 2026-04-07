"""In-memory state persistence."""

import json
from pathlib import Path
from typing import Any


class MemoryState:
    """Singleton in-memory state that persists to temp/memory-state.json."""

    _instance = None
    _state_file = Path("temp/memory-state.json")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._load()
        return cls._instance

    def _load(self):
        if self._state_file.exists():
            with open(self._state_file) as f:
                self._data = json.load(f)

    def _save(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._state_file, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def get_collection(self, name: str) -> list[dict[str, Any]]:
        return self._data.setdefault(name, [])

    def save(self):
        self._save()

    def clear(self):
        self._data = {}
        self._save()
