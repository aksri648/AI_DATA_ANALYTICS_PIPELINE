import pandas as pd
import numpy as np
from app.utils.logging import logger


class DataCleaning:
    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(subset=subset)
        removed = before - len(df)
        if removed:
            logger.info(f"Removed {removed} duplicate rows")
        return df

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        strategy: str = "auto",
        fill_values: dict[str, any] | None = None,
    ) -> pd.DataFrame:
        if strategy == "auto":
            for col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count == 0:
                    continue
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].fillna(method="ffill")
                else:
                    df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown")
        elif strategy == "drop":
            before = len(df)
            df = df.dropna()
            logger.info(f"Dropped {before - len(df)} rows with missing values")
        elif strategy == "fill":
            if fill_values:
                df = df.fillna(fill_values)
        return df

    @staticmethod
    def remove_empty_rows(df: pd.DataFrame, how: str = "all") -> pd.DataFrame:
        before = len(df)
        df = df.dropna(how=how)
        removed = before - len(df)
        if removed:
            logger.info(f"Removed {removed} empty rows")
        return df

    @staticmethod
    def remove_outliers_iqr(df: pd.DataFrame, columns: list[str] | None = None, multiplier: float = 1.5) -> pd.DataFrame:
        cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()
        before = len(df)
        for col in cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - multiplier * IQR
            upper = Q3 + multiplier * IQR
            df = df[(df[col] >= lower) & (df[col] <= upper)]
        removed = before - len(df)
        if removed:
            logger.info(f"Removed {removed} outlier rows using IQR")
        return df

    @staticmethod
    def standardize_text_columns(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        cols = columns or df.select_dtypes(include=["object"]).columns.tolist()
        for col in cols:
            df[col] = df[col].astype(str).str.strip().str.lower()
        return df

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        import re
        df.columns = [
            re.sub(r"[^a-zA-Z0-9_]", "_", str(c)).strip("_").lower()
            for c in df.columns
        ]
        return df

    @staticmethod
    def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
        steps = []
        df = DataCleaning.clean_column_names(df)
        steps.append("Standardized column names")

        df = DataCleaning.remove_duplicates(df)
        steps.append("Removed duplicates")

        df = DataCleaning.remove_empty_rows(df)
        steps.append("Removed empty rows")

        df = DataCleaning.handle_missing_values(df, strategy="auto")
        steps.append("Auto-filled missing values")

        try:
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = pd.to_datetime(df[col], errors="ignore")
            steps.append("Parsed date columns")
        except Exception:
            pass

        logger.info(f"Auto-clean completed: {steps}")
        return df, steps
