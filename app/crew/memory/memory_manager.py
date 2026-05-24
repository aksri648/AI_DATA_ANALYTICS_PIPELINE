from typing import Any
from datetime import datetime
from app.utils.helpers import generate_id


class MemoryManager:
    def __init__(self):
        self.conversations: dict[str, list[dict[str, Any]]] = {}
        self.etl_history: list[dict[str, Any]] = []
        self.analytics_context: dict[str, Any] = {}
        self.schema_cache: dict[str, Any] = {}
        self.workflow_memory: dict[str, Any] = {}

    def add_conversation(self, session_id: str, role: str, content: str):
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        self.conversations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def get_conversation(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.conversations.get(session_id, [])[-limit:]

    def add_etl_log(self, log_entry: dict[str, Any]):
        log_entry["id"] = generate_id()
        log_entry["timestamp"] = datetime.now().isoformat()
        self.etl_history.append(log_entry)

    def get_etl_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.etl_history[-limit:]

    def set_analytics_context(self, key: str, value: Any):
        self.analytics_context[key] = value

    def get_analytics_context(self, key: str, default: Any = None) -> Any:
        return self.analytics_context.get(key, default)

    def cache_schema(self, table_name: str, schema: Any):
        self.schema_cache[table_name] = {
            "schema": schema,
            "cached_at": datetime.now().isoformat(),
        }

    def get_cached_schema(self, table_name: str) -> Any | None:
        cache = self.schema_cache.get(table_name)
        return cache["schema"] if cache else None

    def set_workflow_state(self, key: str, value: Any):
        self.workflow_memory[key] = value

    def get_workflow_state(self, key: str, default: Any = None) -> Any:
        return self.workflow_memory.get(key, default)

    def clear_session(self, session_id: str):
        self.conversations.pop(session_id, None)

    def reset(self):
        self.conversations.clear()
        self.etl_history.clear()
        self.analytics_context.clear()
        self.schema_cache.clear()
        self.workflow_memory.clear()


memory_manager = MemoryManager()
