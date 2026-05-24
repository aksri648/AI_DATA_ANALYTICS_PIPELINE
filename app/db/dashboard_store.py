import json
from datetime import datetime
from typing import Any

import pandas as pd

from app.db.duckdb_manager import duckdb_manager, quote_identifier
from app.utils.logging import logger

DASHBOARDS_TABLE = "_dashboards"


class DashboardStore:
    """Persisted dashboard storage backed by DuckDB."""

    def __init__(self):
        self.db = duckdb_manager
        self._ensure_table()

    def _ensure_table(self):
        if not self.db.table_exists(DASHBOARDS_TABLE):
            self.db.conn.execute(f"""
                CREATE TABLE {quote_identifier(DASHBOARDS_TABLE)} (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    dataset_name VARCHAR NOT NULL,
                    dashboard_type VARCHAR NOT NULL DEFAULT 'auto',
                    kpis_json VARCHAR,
                    charts_html_json VARCHAR,
                    config_json VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Created dashboards persistence table")

    def save(
        self,
        name: str,
        dataset_name: str,
        dashboard_type: str,
        kpis: list[dict[str, Any]],
        charts_html: dict[str, str],
        config: dict[str, Any] | None = None,
    ) -> int:
        existing = self.get_by_name(name)
        now = datetime.now().isoformat()
        kpis_json = json.dumps(kpis)
        charts_json = json.dumps(charts_html)
        config_json = json.dumps(config or {})

        if existing:
            dash_id = existing["id"]
            self.db.conn.execute(
                f"""UPDATE {quote_identifier(DASHBOARDS_TABLE)}
                    SET dataset_name=?, dashboard_type=?, kpis_json=?,
                        charts_html_json=?, config_json=?, updated_at=?
                    WHERE id=?""",
                [dataset_name, dashboard_type, kpis_json, charts_json, config_json, now, dash_id],
            )
            logger.info(f"Updated dashboard '{name}' (id={dash_id})")
            return dash_id

        max_id = self.db.conn.execute(
            f"SELECT COALESCE(MAX(id), 0) FROM {quote_identifier(DASHBOARDS_TABLE)}"
        ).fetchone()[0]
        new_id = max_id + 1

        self.db.conn.execute(
            f"""INSERT INTO {quote_identifier(DASHBOARDS_TABLE)}
                (id, name, dataset_name, dashboard_type, kpis_json, charts_html_json, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [new_id, name, dataset_name, dashboard_type, kpis_json, charts_json, config_json, now, now],
        )
        logger.info(f"Saved dashboard '{name}' (id={new_id})")
        return new_id

    def list_all(self) -> list[dict[str, Any]]:
        rows = self.db.conn.execute(
            f"SELECT id, name, dataset_name, dashboard_type, created_at, updated_at FROM {quote_identifier(DASHBOARDS_TABLE)} ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {
                "id": r[0], "name": r[1], "dataset_name": r[2],
                "dashboard_type": r[3],
                "created_at": str(r[4]), "updated_at": str(r[5]),
            }
            for r in rows
        ]

    def get_by_id(self, dash_id: int) -> dict[str, Any] | None:
        rows = self.db.conn.execute(
            f"SELECT * FROM {quote_identifier(DASHBOARDS_TABLE)} WHERE id=?",
            [dash_id],
        ).fetchall()
        if not rows:
            return None
        return self._row_to_dict(rows[0])

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        rows = self.db.conn.execute(
            f"SELECT * FROM {quote_identifier(DASHBOARDS_TABLE)} WHERE name=?",
            [name],
        ).fetchall()
        if not rows:
            return None
        return self._row_to_dict(rows[0])

    def delete(self, dash_id: int) -> bool:
        existing = self.get_by_id(dash_id)
        if not existing:
            return False
        self.db.conn.execute(
            f"DELETE FROM {quote_identifier(DASHBOARDS_TABLE)} WHERE id=?",
            [dash_id],
        )
        logger.info(f"Deleted dashboard id={dash_id}")
        return True

    def _row_to_dict(self, row: tuple) -> dict[str, Any]:
        return {
            "id": row[0],
            "name": row[1],
            "dataset_name": row[2],
            "dashboard_type": row[3],
            "kpis": json.loads(row[4]) if row[4] else [],
            "charts_html": json.loads(row[5]) if row[5] else {},
            "config": json.loads(row[6]) if row[6] else {},
            "created_at": str(row[7]),
            "updated_at": str(row[8]),
        }


dashboard_store = DashboardStore()
