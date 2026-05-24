from typing import Any
from pathlib import Path
import pandas as pd

from app.etl.ingestion import DataIngestion
from app.etl.cleaning import DataCleaning
from app.etl.transformation import DataTransformation
from app.etl.validation import DataValidation
from app.etl.profiling import DataProfiling
from app.etl.feature_engineering import FeatureEngineering
from app.db.warehouse import warehouse
from app.utils.helpers import generate_id, timestamp_now, sanitize_table_name
from app.utils.logging import logger


class ETLPipelineManager:
    def __init__(self):
        self.pipeline_history: list[dict[str, Any]] = []

    def run_ingestion(
        self, file_path: str | None = None, df: pd.DataFrame | None = None,
        name: str | None = None, sheet_name: str | int = 0
    ) -> dict[str, Any]:
        step_id = generate_id()
        if file_path:
            file_path_str = str(file_path)
            if file_path_str.lower().endswith(".pdf"):
                metadata = DataIngestion.ingest_pdf(file_path, name)
                table_name = sanitize_table_name(name or Path(file_path).stem)
            else:
                metadata = DataIngestion.ingest_file(file_path, name, sheet_name)
                table_name = metadata["table_name"]
        elif df is not None:
            table_name = name or "dataset"
            metadata = DataIngestion.ingest_df(df, table_name)
        else:
            raise ValueError("Either file_path or df must be provided")

        self.pipeline_history.append({
            "id": step_id,
            "step": "ingestion",
            "status": "completed",
            "timestamp": timestamp_now(),
            "table_name": table_name,
            "metadata": metadata,
        })
        return {"status": "success", "table_name": table_name, "metadata": metadata}

    def run_cleaning(self, table_name: str) -> dict[str, Any]:
        step_id = generate_id()
        df = warehouse.get_dataset(table_name)
        cleaned_df, steps = DataCleaning.auto_clean(df)
        warehouse.store_dataset(cleaned_df, f"{table_name}_cleaned")

        validation = DataValidation.validate_dataset(cleaned_df)

        self.pipeline_history.append({
            "id": step_id,
            "step": "cleaning",
            "status": "completed",
            "timestamp": timestamp_now(),
            "table_name": f"{table_name}_cleaned",
            "cleaning_steps": steps,
            "validation": validation,
        })
        return {"status": "success", "cleaning_steps": steps, "validation": validation}

    def run_transformation(
        self, table_name: str,
        transformations: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        step_id = generate_id()
        df = warehouse.get_dataset(table_name)
        if transformations:
            for t in transformations:
                op = t.get("operation")
                params = {k: v for k, v in t.items() if k != "operation"}
                if hasattr(DataTransformation, op):
                    df = getattr(DataTransformation, op)(df, **params)
        else:
            df = DataTransformation.convert_dtypes(df)

        warehouse.store_dataset(df, f"{table_name}_transformed")

        self.pipeline_history.append({
            "id": step_id,
            "step": "transformation",
            "status": "completed",
            "timestamp": timestamp_now(),
            "table_name": f"{table_name}_transformed",
            "transformations": transformations or ["auto_dtype_conversion"],
        })
        return {"status": "success", "row_count": len(df)}

    def run_feature_engineering(
        self, table_name: str,
        numeric_columns: list[str] | None = None,
        date_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        step_id = generate_id()
        df = warehouse.get_dataset(table_name)
        df, new_features = FeatureEngineering.generate_features(df, numeric_columns, date_columns)
        warehouse.store_dataset(df, f"{table_name}_features")

        self.pipeline_history.append({
            "id": step_id,
            "step": "feature_engineering",
            "status": "completed",
            "timestamp": timestamp_now(),
            "table_name": f"{table_name}_features",
            "new_features": new_features,
        })
        return {"status": "success", "new_features": new_features}

    def run_full_etl(
        self, file_path: str | None = None, df: pd.DataFrame | None = None,
        name: str | None = None, sheet_name: str | int = 0,
        run_features: bool = True
    ) -> dict[str, Any]:
        steps = []
        try:
            ingestion = self.run_ingestion(file_path, df, name, sheet_name)
            steps.append(ingestion)
            table_name = ingestion["table_name"]

            cleaning = self.run_cleaning(table_name)
            steps.append(cleaning)

            transformation = self.run_transformation(f"{table_name}_cleaned")
            steps.append(transformation)

            target_table = f"{table_name}_cleaned_transformed"

            if run_features:
                fe = self.run_feature_engineering(target_table)
                steps.append(fe)
                target_table = f"{target_table}_features"

            final = warehouse.get_dataset(target_table)
            profile = DataProfiling.full_profile(final)

            logger.info(f"Full ETL completed: {target_table} with {len(final)} rows")
            return {
                "status": "success",
                "final_table": target_table,
                "final_rows": len(final),
                "steps": steps,
                "profile": profile,
                "pipeline_id": generate_id(),
            }
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            return {"status": "failed", "error": str(e), "steps": steps}

    def get_pipeline_history(self) -> list[dict[str, Any]]:
        return self.pipeline_history

    def profile_dataset(self, table_name: str) -> dict[str, Any]:
        df = warehouse.get_dataset(table_name)
        return DataProfiling.full_profile(df)

    def validate_dataset(self, table_name: str) -> dict[str, Any]:
        df = warehouse.get_dataset(table_name)
        return DataValidation.validate_dataset(df)


etl_pipeline = ETLPipelineManager()
