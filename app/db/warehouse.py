from typing import Any

import pandas as pd

from app.db.duckdb_manager import duckdb_manager, quote_identifier
from app.utils.helpers import sanitize_table_name
from app.utils.logging import logger


class DataWarehouse:
    def __init__(self):
        self.db = duckdb_manager

    def store_dataset(self, df: pd.DataFrame, name: str, metadata: dict[str, Any] | None = None):
        name = sanitize_table_name(name)
        self.db.register_table(df, name)
        if metadata:
            meta_table = f"{name}_metadata"
            meta_df = pd.DataFrame([metadata]) if isinstance(metadata, dict) else pd.DataFrame(metadata)
            self.db.register_table(meta_df, meta_table, replace=True)
        logger.info(f"Stored dataset '{name}' with {len(df)} rows")

    def get_dataset(self, name: str) -> pd.DataFrame:
        name = sanitize_table_name(name)
        return self.db.query(f"SELECT * FROM {quote_identifier(name)}")

    def list_datasets(self) -> list[str]:
        return [t for t in self.db.list_tables() if not t.endswith("_metadata")]

    def get_metadata(self, name: str) -> dict[str, Any] | None:
        name = sanitize_table_name(name)
        meta_table = f"{name}_metadata"
        if self.db.table_exists(meta_table):
            df = self.db.query(f"SELECT * FROM {quote_identifier(meta_table)}")
            if not df.empty:
                return df.iloc[0].to_dict()
        return None

    def get_profile(self, name: str) -> pd.DataFrame:
        name = sanitize_table_name(name)
        return self.db.query(f"DESCRIBE {quote_identifier(name)}")

    def query(self, sql: str) -> pd.DataFrame:
        return self.db.query(sql)

    def delete_dataset(self, name: str):
        name = sanitize_table_name(name)
        self.db.drop_table(name)
        self.db.drop_table(f"{name}_metadata")
        logger.info(f"Deleted dataset '{name}'")

    def dag_status(self) -> dict[str, Any]:
        datasets = self.list_datasets()
        info = {}
        for ds in datasets:
            try:
                stats = self.db.get_table_stats(ds)
                info[ds] = stats
            except Exception:
                info[ds] = {"error": "unavailable"}
        return {"datasets": info, "count": len(datasets)}


warehouse = DataWarehouse()
