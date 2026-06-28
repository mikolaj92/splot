from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import SplotState
from .state import load_state_file, write_state_file


class StateStore(Protocol):
    def load(self, session_id: str | None = None) -> SplotState:
        ...

    def save(self, state: SplotState) -> None:
        ...


class MemoryStateStore:
    def __init__(self) -> None:
        self._states: dict[str, SplotState] = {}

    def load(self, session_id: str | None = None) -> SplotState:
        if session_id and session_id in self._states:
            return SplotState.from_dict(self._states[session_id].to_dict())
        return SplotState(session_id=session_id) if session_id else SplotState()

    def save(self, state: SplotState) -> None:
        self._states[state.session_id] = SplotState.from_dict(state.to_dict())


class JsonFileStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self, session_id: str | None = None) -> SplotState:
        state = load_state_file(self.path)
        if session_id and state.session_id != session_id:
            return SplotState(session_id=session_id)
        return state

    def save(self, state: SplotState) -> None:
        write_state_file(self.path, state)

