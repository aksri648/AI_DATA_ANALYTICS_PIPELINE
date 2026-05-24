import pandas as pd
import numpy as np
from typing import Any
from app.utils.logging import logger


class DataValidation:
    @staticmethod
    def check_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> dict[str, Any]:
        dups = df.duplicated(subset=subset, keep=False)
        count = int(dups.sum())
        return {
            "has_duplicates": count > 0,
            "duplicate_count": count,
            "duplicate_percentage": round(count / len(df) * 100, 2) if len(df) > 0 else 0,
        }

    @staticmethod
    def check_missing_values(df: pd.DataFrame) -> dict[str, Any]:
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        return {
            "total_missing": int(null_counts.sum()),
            "columns_with_missing": len(null_cols),
            "missing_by_column": null_cols.to_dict(),
        }

    @staticmethod
    def check_outliers_zscore(df: pd.DataFrame, threshold: float = 3.0) -> dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outliers = {}
        for col in numeric_cols:
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            outlier_count = int((z_scores > threshold).sum())
            if outlier_count > 0:
                outliers[col] = {
                    "count": outlier_count,
                    "percentage": round(outlier_count / len(df) * 100, 2),
                }
        return {"has_outliers": len(outliers) > 0, "outliers": outliers}

    @staticmethod
    def check_schema_compliance(
        df: pd.DataFrame, expected_schema: dict[str, str]
    ) -> dict[str, Any]:
        issues = []
        for col, expected_dtype in expected_schema.items():
            if col not in df.columns:
                issues.append({"column": col, "issue": "missing"})
            else:
                actual = str(df[col].dtype)
                if expected_dtype != actual:
                    issues.append({"column": col, "issue": f"expected {expected_dtype}, got {actual}"})
        return {"compliant": len(issues) == 0, "issues": issues}

    @staticmethod
    def validate_dataset(df: pd.DataFrame) -> dict[str, Any]:
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {str(c): str(d) for c, d in df.dtypes.items()},
            "duplicates": DataValidation.check_duplicates(df),
            "missing_values": DataValidation.check_missing_values(df),
            "outliers": DataValidation.check_outliers_zscore(df),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        }

    @staticmethod
    def detect_anomalies(df: pd.DataFrame, columns: list[str] | None = None) -> list[dict[str, Any]]:
        anomalies = []
        numeric_cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 3 * IQR
            upper = Q3 + 3 * IQR
            anomalous = df[(df[col] < lower) | (df[col] > upper)]
            if len(anomalous) > 0:
                anomalies.append({
                    "column": col,
                    "anomaly_count": len(anomalous),
                    "lower_bound": float(lower),
                    "upper_bound": float(upper),
                    "anomaly_indices": anomalous.index.tolist()[:10],
                })
        return anomalies

    @staticmethod
    def generate_quality_report(df: pd.DataFrame) -> str:
        validation = DataValidation.validate_dataset(df)
        report_parts = [
            "DATA QUALITY REPORT",
            "=" * 50,
            f"Rows: {validation['row_count']}",
            f"Columns: {validation['column_count']}",
            f"Memory: {validation['memory_usage_mb']} MB",
            "",
            "DUPLICATES:",
            f"  {'PASS' if not validation['duplicates']['has_duplicates'] else 'FAIL'} - {validation['duplicates']['duplicate_count']} duplicates ({validation['duplicates']['duplicate_percentage']}%)",
            "",
            "MISSING VALUES:",
            f"  Total missing: {validation['missing_values']['total_missing']}",
        ]
        for col, count in validation["missing_values"].get("missing_by_column", {}).items():
            report_parts.append(f"  - {col}: {count}")
        report_parts.extend([
            "",
            "OUTLIERS:",
        ])
        for col, info in validation["outliers"].get("outliers", {}).items():
            report_parts.append(f"  - {col}: {info['count']} outliers ({info['percentage']}%)")
        return "\n".join(report_parts)
