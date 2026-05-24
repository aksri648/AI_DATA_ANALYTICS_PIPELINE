import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any
from app.charts.chart_engine import chart_engine
from app.utils.logging import logger


class DashboardBuilder:
    @staticmethod
    def create_sales_dashboard(df: pd.DataFrame, date_col: str, sales_col: str, category_col: str | None = None) -> dict[str, Any]:
        charts = {}
        if date_col in df.columns:
            ts = df.groupby(date_col)[sales_col].sum().reset_index()
            charts["revenue_trend"] = chart_engine.create_line_chart(ts, x=date_col, y=sales_col, title="Revenue Trend")
        if category_col and category_col in df.columns:
            cat_sales = df.groupby(category_col)[sales_col].sum().reset_index()
            charts["sales_by_category"] = chart_engine.create_pie_chart(
                cat_sales, names=category_col, values=sales_col, title="Sales by Category"
            )
        kpis = chart_engine.generate_kpi_cards(df, [sales_col])
        return {"charts": charts, "kpis": kpis, "type": "sales"}

    @staticmethod
    def create_finance_dashboard(df: pd.DataFrame, date_col: str, metrics: list[str]) -> dict[str, Any]:
        charts = {}
        if date_col in df.columns:
            for metric in metrics:
                if metric in df.columns:
                    ts = df.groupby(date_col)[metric].sum().reset_index()
                    charts[f"{metric}_trend"] = chart_engine.create_line_chart(
                        ts, x=date_col, y=metric, title=f"{metric.replace('_', ' ').title()} Trend"
                    )
        kpis = chart_engine.generate_kpi_cards(df, metrics)
        charts["correlation"] = chart_engine.create_heatmap(df[metrics] if all(m in df.columns for m in metrics) else df)
        return {"charts": charts, "kpis": kpis, "type": "finance"}

    @staticmethod
    def create_hr_dashboard(df: pd.DataFrame, dept_col: str, salary_col: str, name_col: str | None = None) -> dict[str, Any]:
        charts = {}
        if dept_col in df.columns and salary_col in df.columns:
            dept_stats = df.groupby(dept_col)[salary_col].agg(["mean", "sum", "count"]).reset_index()
            charts["salary_by_dept"] = chart_engine.create_bar_chart(
                dept_stats, x=dept_col, y="mean", title="Avg Salary by Department"
            )
            charts["headcount"] = chart_engine.create_pie_chart(
                dept_stats, names=dept_col, values="count", title="Headcount by Department"
            )
        kpis = chart_engine.generate_kpi_cards(df, [salary_col] if salary_col in df.columns else None)
        return {"charts": charts, "kpis": kpis, "type": "hr"}

    @staticmethod
    def create_marketing_dashboard(df: pd.DataFrame, channel_col: str, spend_col: str, conversion_col: str | None = None) -> dict[str, Any]:
        charts = {}
        if channel_col in df.columns and spend_col in df.columns:
            channel_stats = df.groupby(channel_col)[spend_col].sum().reset_index()
            charts["spend_by_channel"] = chart_engine.create_bar_chart(
                channel_stats, x=channel_col, y=spend_col, title="Marketing Spend by Channel"
            )
        if conversion_col and conversion_col in df.columns:
            charts["conversion_hist"] = chart_engine.create_histogram(df, x=conversion_col, title="Conversion Rate Distribution")
        kpis = chart_engine.generate_kpi_cards(df, [spend_col, conversion_col] if conversion_col else [spend_col])
        return {"charts": charts, "kpis": kpis, "type": "marketing"}

    @staticmethod
    def auto_dashboard(df: pd.DataFrame, dashboard_type: str = "auto") -> dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        if dashboard_type == "sales" and date_cols and numeric_cols:
            cat = categorical_cols[0] if categorical_cols else None
            return DashboardBuilder.create_sales_dashboard(df, date_cols[0], numeric_cols[0], cat)
        elif dashboard_type == "finance" and date_cols and len(numeric_cols) >= 2:
            return DashboardBuilder.create_finance_dashboard(df, date_cols[0], numeric_cols[:3])
        elif dashboard_type == "hr" and categorical_cols and numeric_cols:
            return DashboardBuilder.create_hr_dashboard(df, categorical_cols[0], numeric_cols[0])
        elif dashboard_type == "marketing" and categorical_cols and numeric_cols:
            conversion = numeric_cols[1] if len(numeric_cols) > 1 else None
            return DashboardBuilder.create_marketing_dashboard(df, categorical_cols[0], numeric_cols[0], conversion)

        charts = {}
        charts["auto_chart"] = chart_engine.auto_chart(df, "overview")
        kpis = chart_engine.generate_kpi_cards(df, numeric_cols[:4])
        if len(numeric_cols) >= 2:
            charts["correlation"] = chart_engine.create_heatmap(df, title="Correlation Heatmap")
        return {"charts": charts, "kpis": kpis, "type": "auto"}

    @staticmethod
    def to_html_dict(dashboard: dict[str, Any]) -> dict[str, str]:
        """Convert plotly figure objects in a dashboard to HTML strings for persistence."""
        charts = dashboard.get("charts", {})
        charts_html = {}
        for name, fig in charts.items():
            if fig is not None:
                charts_html[name] = chart_engine.figure_to_html(fig)
        return charts_html


dashboard_builder = DashboardBuilder()
