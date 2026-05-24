import pandas as pd
import numpy as np
from typing import Any
from app.utils.logging import logger


class FeatureEngineering:
    @staticmethod
    def create_ratios(df: pd.DataFrame, numerator: str, denominator: str, new_name: str | None = None) -> pd.DataFrame:
        name = new_name or f"{numerator}_to_{denominator}_ratio"
        df[name] = df[numerator] / df[denominator].replace(0, np.nan)
        df[name] = df[name].fillna(0)
        return df

    @staticmethod
    def create_running_total(df: pd.DataFrame, column: str, group_by: str | None = None) -> pd.DataFrame:
        name = f"{column}_running_total"
        if group_by:
            df[name] = df.groupby(group_by)[column].cumsum()
        else:
            df[name] = df[column].cumsum()
        return df

    @staticmethod
    def create_lag(df: pd.DataFrame, column: str, periods: int = 1, group_by: str | None = None) -> pd.DataFrame:
        name = f"{column}_lag_{periods}"
        if group_by:
            df[name] = df.groupby(group_by)[column].shift(periods)
        else:
            df[name] = df[column].shift(periods)
        return df

    @staticmethod
    def create_pct_change(df: pd.DataFrame, column: str, periods: int = 1, group_by: str | None = None) -> pd.DataFrame:
        name = f"{column}_pct_change_{periods}"
        if group_by:
            df[name] = df.groupby(group_by)[column].pct_change(periods) * 100
        else:
            df[name] = df[column].pct_change(periods) * 100
        return df

    @staticmethod
    def create_rolling_avg(df: pd.DataFrame, column: str, window: int = 3) -> pd.DataFrame:
        name = f"{column}_rolling_avg_{window}"
        df[name] = df[column].rolling(window=window).mean()
        return df

    @staticmethod
    def create_cumulative_metrics(df: pd.DataFrame, column: str) -> pd.DataFrame:
        df[f"{column}_cumsum"] = df[column].cumsum()
        df[f"{column}_cummax"] = df[column].cummax()
        df[f"{column}_cummin"] = df[column].cummin()
        return df

    @staticmethod
    def encode_cyclical_features(df: pd.DataFrame, column: str, max_value: int | None = None) -> pd.DataFrame:
        if max_value is None:
            if df[column].dtype in ("int", "float"):
                max_value = df[column].max()
            else:
                return df
        df[f"{column}_sin"] = np.sin(2 * np.pi * df[column] / max_value)
        df[f"{column}_cos"] = np.cos(2 * np.pi * df[column] / max_value)
        return df

    @staticmethod
    def generate_features(
        df: pd.DataFrame,
        numeric_columns: list[str] | None = None,
        date_columns: list[str] | None = None,
    ) -> tuple[pd.DataFrame, list[str]]:
        new_features = []
        if numeric_columns:
            for col in numeric_columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    df = FeatureEngineering.create_cumulative_metrics(df, col)
                    new_features.extend([f"{col}_cumsum", f"{col}_cummax", f"{col}_cummin"])
                    df = FeatureEngineering.create_rolling_avg(df, col)
                    new_features.append(f"{col}_rolling_avg_3")
        if date_columns:
            for col in date_columns:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        continue
                    df[f"{col}_year"] = df[col].dt.year
                    df[f"{col}_month"] = df[col].dt.month
                    df[f"{col}_day"] = df[col].dt.day
                    df[f"{col}_quarter"] = df[col].dt.quarter
                    df[f"{col}_dayofweek"] = df[col].dt.dayofweek
                    new_features.extend([
                        f"{col}_year", f"{col}_month", f"{col}_day",
                        f"{col}_quarter", f"{col}_dayofweek",
                    ])
        return df, new_features
