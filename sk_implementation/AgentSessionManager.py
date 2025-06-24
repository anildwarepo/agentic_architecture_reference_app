from typing import Callable, Dict, Generic, TypeVar

T = TypeVar("T")  

class MultiAgentSessionManager(Generic[T]):
    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._sessions: Dict[str, T] = {}

    def get_or_create_session(self, conversation_id: str) -> T:
        if conversation_id not in self._sessions:
            print(f"session with {conversation_id} not found")
            self._sessions[conversation_id] = self._factory()
        return self._sessions[conversation_id]