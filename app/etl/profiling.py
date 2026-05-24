import pandas as pd
import numpy as np
from typing import Any
from app.utils.logging import logger


class DataProfiling:
    @staticmethod
    def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            return pd.DataFrame()
        stats = numeric.describe(percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]).T
        stats["skewness"] = numeric.skew()
        stats["kurtosis"] = numeric.kurtosis()
        stats["missing"] = numeric.isnull().sum()
        stats["missing_pct"] = (numeric.isnull().sum() / len(numeric) * 100).round(2)
        return stats

    @staticmethod
    def correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] < 2:
            return pd.DataFrame()
        return numeric.corr(method=method)

    @staticmethod
    def value_counts_profile(df: pd.DataFrame, top_n: int = 10) -> dict[str, Any]:
        profile = {}
        for col in df.columns:
            counts = df[col].value_counts().head(top_n)
            profile[col] = {
                "unique": int(df[col].nunique()),
                "top_values": counts.to_dict(),
                "dtype": str(df[col].dtype),
            }
        return profile

    @staticmethod
    def missing_patterns(df: pd.DataFrame) -> pd.DataFrame:
        missing_matrix = df.isnull()
        missing_counts = missing_matrix.sum().sort_values(ascending=False)
        missing_df = missing_counts[missing_counts > 0].reset_index()
        missing_df.columns = ["column", "missing_count"]
        missing_df["missing_pct"] = (missing_df["missing_count"] / len(df) * 100).round(2)
        return missing_df

    @staticmethod
    def full_profile(df: pd.DataFrame) -> dict[str, Any]:
        return {
            "overview": {
                "rows": len(df),
                "columns": len(df.columns),
                "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                "duplicate_rows": int(df.duplicated().sum()),
                "duplicate_pct": round(df.duplicated().sum() / len(df) * 100, 2) if len(df) > 0 else 0,
            },
            "column_types": {str(c): str(d) for c, d in df.dtypes.items()},
            "missing_summary": {
                "total_missing": int(df.isnull().sum().sum()),
                "columns_with_missing": int((df.isnull().sum() > 0).sum()),
            },
            "numeric_stats": DataProfiling.descriptive_stats(df).to_dict() if not df.select_dtypes(include=[np.number]).empty else {},
            "correlation": DataProfiling.correlation_matrix(df).to_dict() if df.select_dtypes(include=[np.number]).shape[1] >= 2 else {},
            "value_counts": DataProfiling.value_counts_profile(df),
        }

    @staticmethod
    def generate_profiling_report(df: pd.DataFrame) -> str:
        profile = DataProfiling.full_profile(df)
        lines = [
            "DATA PROFILING REPORT",
            "=" * 60,
            "",
            "OVERVIEW",
            "-" * 40,
            f"  Rows: {profile['overview']['rows']:,}",
            f"  Columns: {profile['overview']['columns']}",
            f"  Memory: {profile['overview']['memory_mb']} MB",
            f"  Duplicates: {profile['overview']['duplicate_rows']} ({profile['overview']['duplicate_pct']}%)",
            "",
            "COLUMN TYPES",
            "-" * 40,
        ]
        for col, dtype in profile["column_types"].items():
            lines.append(f"  {col}: {dtype}")
        lines.extend([
            "",
            "MISSING VALUES",
            "-" * 40,
            f"  Total missing: {profile['missing_summary']['total_missing']}",
            f"  Columns with missing: {profile['missing_summary']['columns_with_missing']}",
        ])
        if profile.get("numeric_stats"):
            lines.extend(["", "NUMERIC STATS", "-" * 40])
            for col, stats in list(profile["numeric_stats"].items())[:5]:
                lines.append(f"  {col}:")
                for k, v in stats.items():
                    if isinstance(v, (int, float)):
                        lines.append(f"    {k}: {v:.2f}")
        return "\n".join(lines)
