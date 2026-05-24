import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def generate_id() -> str:
    return str(uuid.uuid4())


def generate_file_hash(file_path: str | Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def timestamp_now() -> str:
    return datetime.now().isoformat()


def safe_json_loads(data: str) -> dict[str, Any] | None:
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def truncate_text(text: str, max_length: int = 200) -> str:
    return text[:max_length] + "..." if len(text) > max_length else text


def bytes_to_mb(size_bytes: int) -> float:
    return round(size_bytes / (1024 * 1024), 2)


def validate_file_extension(filename: str, allowed: list[str]) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in allowed


def sanitize_table_name(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name).lower()


def chunk_list(lst: list, chunk_size: int):
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]
