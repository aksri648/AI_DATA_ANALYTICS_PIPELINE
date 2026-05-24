from typing import Any
from datetime import datetime
from app.utils.helpers import generate_id


class SessionService:
    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}

    def create_session(self) -> str:
        session_id = generate_id()
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "files": [],
            "tables": [],
            "chat_history": [],
            "etl_history": [],
            "dashboards": [],
            "reports": [],
        }
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self.sessions.get(session_id)

    def update_session(self, session_id: str, key: str, value: Any):
        if session_id in self.sessions:
            self.sessions[session_id][key] = value
            self.sessions[session_id]["last_active"] = datetime.now().isoformat()

    def add_file(self, session_id: str, file_info: dict[str, Any]):
        if session_id in self.sessions:
            self.sessions[session_id]["files"].append(file_info)
            self.sessions[session_id]["last_active"] = datetime.now().isoformat()

    def add_table(self, session_id: str, table_name: str):
        if session_id in self.sessions and table_name not in self.sessions[session_id]["tables"]:
            self.sessions[session_id]["tables"].append(table_name)

    def add_chat(self, session_id: str, role: str, content: str):
        if session_id in self.sessions:
            self.sessions[session_id]["chat_history"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })

    def get_chat_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        session = self.sessions.get(session_id)
        if session:
            return session["chat_history"][-limit:]
        return []

    def clear_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    def list_sessions(self) -> list[str]:
        return list(self.sessions.keys())


session_service = SessionService()
