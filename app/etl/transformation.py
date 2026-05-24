import pandas as pd
import numpy as np
from app.utils.logging import logger


class DataTransformation:
    @staticmethod
    def normalize_numeric(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()
        for col in cols:
            if df[col].std() > 0:
                df[col] = (df[col] - df[col].mean()) / df[col].std()
        return df

    @staticmethod
    def one_hot_encode(df: pd.DataFrame, columns: list[str] | None = None, max_categories: int = 10) -> pd.DataFrame:
        cols = columns or df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cols:
            if df[col].nunique() <= max_categories:
                dummies = pd.get_dummies(df[col], prefix=col)
                df = pd.concat([df, dummies], axis=1)
                df = df.drop(columns=[col])
            else:
                logger.warning(f"Skipping one-hot for {col}: {df[col].nunique()} categories > {max_categories}")
        return df

    @staticmethod
    def parse_dates(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        cols = columns or df.select_dtypes(include=["object"]).columns.tolist()
        for col in cols:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass
        return df

    @staticmethod
    def convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = pd.to_numeric(df[col], errors="ignore")
                except Exception:
                    pass
        df = df.infer_objects()
        return df

    @staticmethod
    def add_date_features(df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        df[date_column] = pd.to_datetime(df[date_column])
        df[f"{date_column}_year"] = df[date_column].dt.year
        df[f"{date_column}_month"] = df[date_column].dt.month
        df[f"{date_column}_day"] = df[date_column].dt.day
        df[f"{date_column}_quarter"] = df[date_column].dt.quarter
        df[f"{date_column}_dayofweek"] = df[date_column].dt.dayofweek
        df[f"{date_column}_weekday"] = (df[date_column].dt.dayofweek < 5).astype(int)
        return df

    @staticmethod
    def aggregate(
        df: pd.DataFrame,
        group_by: list[str],
        aggregations: dict[str, str],
    ) -> pd.DataFrame:
        return df.groupby(group_by).agg(aggregations).reset_index()

    @staticmethod
    def pivot(df: pd.DataFrame, index: str, columns: str, values: str, aggfunc: str = "mean") -> pd.DataFrame:
        return df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc).reset_index()

    @staticmethod
    def melt(df: pd.DataFrame, id_vars: list[str], value_vars: list[str] | None = None) -> pd.DataFrame:
        return df.melt(id_vars=id_vars, value_vars=value_vars)

    @staticmethod
    def sort_values(df: pd.DataFrame, by: list[str], ascending: bool = True) -> pd.DataFrame:
        return df.sort_values(by=by, ascending=ascending)

    @staticmethod
    def rank_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        for col in columns:
            df[f"{col}_rank"] = df[col].rank(ascending=False)
        return df

    @staticmethod
    def create_bins(df: pd.DataFrame, column: str, bins: int, labels: list[str] | None = None) -> pd.DataFrame:
        df[f"{column}_binned"] = pd.cut(df[column], bins=bins, labels=labels)
        return df
