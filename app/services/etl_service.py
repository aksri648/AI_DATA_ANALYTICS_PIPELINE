from typing import Any
import pandas as pd

from app.etl.pipeline_manager import etl_pipeline
from app.db.warehouse import warehouse
from app.charts.chart_engine import chart_engine
from app.charts.dashboard_builder import dashboard_builder
from app.etl.profiling import DataProfiling
from app.etl.validation import DataValidation
from app.utils.logging import logger


class ETLService:
    def ingest_file(self, file_path: str, table_name: str | None = None) -> dict[str, Any]:
        return etl_pipeline.run_ingestion(file_path=file_path, name=table_name)

    def ingest_df(self, df: pd.DataFrame, name: str) -> dict[str, Any]:
        return etl_pipeline.run_ingestion(df=df, name=name)

    def run_full_etl(self, file_path: str | None = None, df: pd.DataFrame | None = None, name: str | None = None) -> dict[str, Any]:
        return etl_pipeline.run_full_etl(file_path=file_path, df=df, name=name)

    def clean_dataset(self, table_name: str) -> dict[str, Any]:
        return etl_pipeline.run_cleaning(table_name)

    def profile_dataset(self, table_name: str) -> dict[str, Any]:
        return etl_pipeline.profile_dataset(table_name)

    def validate_dataset(self, table_name: str) -> dict[str, Any]:
        return etl_pipeline.validate_dataset(table_name)

    def list_datasets(self) -> list[str]:
        return warehouse.list_datasets()

    def get_preview(self, table_name: str, n: int = 10) -> pd.DataFrame:
        return warehouse.get_dataset(table_name).head(n)

    def get_dataset(self, table_name: str) -> pd.DataFrame:
        return warehouse.get_dataset(table_name)

    def get_pipeline_history(self) -> list[dict[str, Any]]:
        return etl_pipeline.get_pipeline_history()


etl_service = ETLService()
