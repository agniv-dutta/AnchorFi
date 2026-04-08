from __future__ import annotations

import json
from datetime import date
from typing import Any


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def _key(self, target: str, day: date) -> str:
        return f"{target.strip().lower()}::{day.isoformat()}"

    def get(self, target: str, day: date) -> dict[str, Any] | None:
        return self._store.get(self._key(target, day))

    def set(self, target: str, day: date, value: dict[str, Any]) -> None:
        self._store[self._key(target, day)] = value


def dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads_json(text: str) -> Any:
    return json.loads(text)

