import os
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from app.config.settings import DUCKDB_PATH
from app.utils.logging import logger


class DuckDBManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DUCKDB_PATH
        self._conn: duckdb.DuckDBPyConnection | None = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
            self._conn.execute("SET enable_progress_bar=false;")
        return self._conn

    def query(self, sql: str) -> pd.DataFrame:
        return self.conn.execute(sql).fetchdf()

    def query_raw(self, sql: str) -> list[Any]:
        return self.conn.execute(sql).fetchall()

    def register_table(self, df: pd.DataFrame, table_name: str, replace: bool = True):
        if replace:
            existing = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                [table_name],
            ).fetchone()
            if existing:
                self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.conn.register("_temp_df", df)
        self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _temp_df")

    def load_csv(self, file_path: str, table_name: str) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        self.register_table(df, table_name)
        logger.info(f"Loaded CSV {file_path} into table {table_name}")
        return df

    def load_excel(self, file_path: str, table_name: str, sheet_name: str | int = 0) -> pd.DataFrame:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        self.register_table(df, table_name)
        logger.info(f"Loaded Excel {file_path} into table {table_name}")
        return df

    def list_tables(self) -> list[str]:
        result = self.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        return [r[0] for r in result]

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
        return [
            {"name": r[0], "type": r[1], "nullable": r[2] == "YES"}
            for r in result
        ]

    def get_table_stats(self, table_name: str) -> dict[str, Any]:
        row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        col_count = len(self.get_table_schema(table_name))
        return {"row_count": row_count, "column_count": col_count}

    def table_exists(self, table_name: str) -> bool:
        result = self.conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='main' AND table_name=?",
            [table_name],
        ).fetchone()
        return result[0] > 0

    def drop_table(self, table_name: str):
        if self.table_exists(table_name):
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


duckdb_manager = DuckDBManager()
