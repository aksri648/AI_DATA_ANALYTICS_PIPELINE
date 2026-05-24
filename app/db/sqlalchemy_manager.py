from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.utils.logging import logger


class SQLAlchemyManager:
    def __init__(self, connection_url: str | None = None):
        self.connection_url = connection_url
        self._engine: Engine | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None and self.connection_url:
            self._engine = create_engine(self.connection_url)
        if self._engine is None:
            raise ValueError("No connection URL configured")
        return self._engine

    def connect(self, connection_url: str):
        self.connection_url = connection_url
        self._engine = create_engine(connection_url)
        logger.info(f"Connected to database")

    def disconnect(self):
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def test_connection(self, connection_url: str | None = None) -> bool:
        try:
            eng = create_engine(connection_url or self.connection_url)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            eng.dispose()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def list_tables(self) -> list[str]:
        insp = inspect(self.engine)
        return insp.get_table_names()

    def get_schema(self, table_name: str) -> list[dict[str, Any]]:
        insp = inspect(self.engine)
        columns = insp.get_columns(table_name)
        return [
            {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)}
            for c in columns
        ]

    def query(self, sql: str) -> pd.DataFrame:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df

    def execute_read_only(self, sql: str) -> list[tuple]:
        if not sql.strip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are permitted")
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            return [tuple(row) for row in result.fetchall()]

    def write_df(self, df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
        df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
        logger.info(f"Written {len(df)} rows to {table_name}")

    def get_table_info(self, table_name: str) -> dict[str, Any]:
        schema = self.get_schema(table_name)
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        with self.engine.connect() as conn:
            row_count = conn.execute(text(query)).scalar()
        return {
            "table_name": table_name,
            "columns": schema,
            "row_count": row_count,
            "column_count": len(schema),
        }
