import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any
from app.charts.chart_engine import chart_engine
from app.utils.logging import logger


class DashboardBuilder:
    """Builds comprehensive PowerBI-style dashboards with diverse chart types."""

    @staticmethod
    def create_sales_dashboard(df: pd.DataFrame, date_col: str, sales_col: str, category_col: str | None = None) -> dict[str, Any]:
        charts = {}
        if date_col in df.columns:
            ts = df.groupby(date_col)[sales_col].sum().reset_index()
            charts["revenue_trend"] = chart_engine.create_line_chart(ts, x=date_col, y=sales_col, title="Revenue Trend")
            if len(ts) >= 10:
                window = min(7, len(ts) // 3) or 3
                charts["revenue_rolling"] = chart_engine.create_rolling_average_line(ts, x=date_col, y=sales_col, window=window, title=f"Revenue Trend ({window}-period Avg)")
            charts["revenue_cumulative"] = chart_engine.create_cumulative_line(ts, x=date_col, y=sales_col, title="Cumulative Revenue")
        if category_col and category_col in df.columns:
            cat_sales = df.groupby(category_col)[sales_col].sum().reset_index()
            charts["sales_by_category"] = chart_engine.create_pie_chart(cat_sales, names=category_col, values=sales_col, title="Sales by Category")
            charts["sales_by_category_bar"] = chart_engine.create_bar_chart(cat_sales, x=category_col, y=sales_col, title="Sales by Category (Bar)")
        if date_col in df.columns and category_col and category_col in df.columns:
            grp = df.groupby([date_col, category_col])[sales_col].sum().reset_index()
            charts["stacked_trend"] = chart_engine.create_stacked_bar(grp, x=date_col, y=sales_col, color=category_col, title="Revenue by Category Over Time")
        kpis = chart_engine.generate_kpi_cards(df, [sales_col])
        return {"charts": charts, "kpis": kpis, "type": "sales"}

    @staticmethod
    def create_finance_dashboard(df: pd.DataFrame, date_col: str, metrics: list[str]) -> dict[str, Any]:
        charts = {}
        if date_col in df.columns:
            ts = df.groupby(date_col)[metrics].sum().reset_index().sort_values(date_col)
            if len(metrics) >= 2:
                charts["multi_trend"] = chart_engine.create_multi_line(ts, x=date_col, y=metrics, title="All Metrics Over Time")
            for metric in metrics[:3]:
                if metric in df.columns:
                    charts[f"{metric}_trend"] = chart_engine.create_line_chart(ts, x=date_col, y=metric, title=f"{metric.replace('_', ' ').title()} Trend")
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] >= 2:
            charts["correlation"] = chart_engine.create_heatmap(df, title="Correlation Heatmap")
        for col in metrics[:2]:
            if col in df.columns:
                charts[f"dist_{col}"] = chart_engine.create_histogram(df, x=col, title=f"Distribution: {col.replace('_', ' ').title()}")
        kpis = chart_engine.generate_kpi_cards(df, metrics)
        return {"charts": charts, "kpis": kpis, "type": "finance"}

    @staticmethod
    def create_hr_dashboard(df: pd.DataFrame, dept_col: str, salary_col: str, name_col: str | None = None) -> dict[str, Any]:
        charts = {}
        if dept_col in df.columns and salary_col in df.columns:
            dept_stats = df.groupby(dept_col)[salary_col].agg(["mean", "sum", "count"]).reset_index()
            charts["salary_by_dept"] = chart_engine.create_bar_chart(dept_stats, x=dept_col, y="mean", title="Avg Salary by Department")
            charts["headcount"] = chart_engine.create_pie_chart(dept_stats, names=dept_col, values="count", title="Headcount by Department")
        kpis = chart_engine.generate_kpi_cards(df, [salary_col] if salary_col in df.columns else None)
        return {"charts": charts, "kpis": kpis, "type": "hr"}

    @staticmethod
    def create_marketing_dashboard(df: pd.DataFrame, channel_col: str, spend_col: str, conversion_col: str | None = None) -> dict[str, Any]:
        charts = {}
        if channel_col in df.columns and spend_col in df.columns:
            channel_stats = df.groupby(channel_col)[spend_col].sum().reset_index()
            charts["spend_by_channel"] = chart_engine.create_bar_chart(channel_stats, x=channel_col, y=spend_col, title="Marketing Spend by Channel")
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

        return DashboardBuilder._build_comprehensive_dashboard(df, numeric_cols, categorical_cols, date_cols)

    @staticmethod
    def _build_comprehensive_dashboard(
        df: pd.DataFrame,
        numeric_cols: list[str],
        categorical_cols: list[str],
        date_cols: list[str],
    ) -> dict[str, Any]:
        """Build a comprehensive auto-dashboard with 10-15+ diverse charts."""
        charts: dict[str, Any] = {}

        # ── 1. KPI GAUGES ────────────────────────────────────────────
        total_cells = len(df) * len(df.columns)
        missing_cells = int(df.isnull().sum().sum())
        completeness = round(((total_cells - missing_cells) / total_cells) * 100, 1) if total_cells else 0
        duplicate_pct = round(df.duplicated().sum() / len(df) * 100, 1) if len(df) > 0 else 0
        charts["gauge_completeness"] = chart_engine.create_gauge_chart(completeness, title="Data Completeness %", suffix="%")
        charts["gauge_uniqueness"] = chart_engine.create_gauge_chart(100 - duplicate_pct, title="Data Uniqueness %", suffix="%")

        # ── 2. CORRELATION HEATMAP ───────────────────────────────────
        if len(numeric_cols) >= 2:
            charts["correlation_heatmap"] = chart_engine.create_heatmap(df, title="Correlation Heatmap")

        # ── 3. HISTOGRAMS (distributions for each numeric) ───────────
        for col in numeric_cols[:4]:
            charts[f"hist_{col}"] = chart_engine.create_histogram(df, x=col, title=f"Distribution: {col.replace('_', ' ').title()}")

        # ── 4. BOX PLOTS (outlier detection) ─────────────────────────
        for col in numeric_cols[:3]:
            charts[f"box_{col}"] = chart_engine.create_box_plot(df, x=None, y=col, title=f"Box Plot: {col.replace('_', ' ').title()}")

        # ── 5. BAR CHARTS (categorical breakdowns) ───────────────────
        for col in categorical_cols[:4]:
            vc = df[col].value_counts().head(12).reset_index()
            vc.columns = [col, "count"]
            charts[f"bar_{col}"] = chart_engine.create_bar_chart(vc, x=col, y="count", title=f"Count by {col.replace('_', ' ').title()}")

        # ── 6. AGGREGATED BARS (sum of numeric by category) ─────────
        if categorical_cols and numeric_cols:
            cat = categorical_cols[0]
            for ncol in numeric_cols[:2]:
                agg = df.groupby(cat)[ncol].sum().reset_index().head(12)
                agg.columns = [cat, ncol]
                charts[f"sum_{ncol}_by_{cat}"] = chart_engine.create_bar_chart(agg, x=cat, y=ncol, title=f"Total {ncol.replace('_', ' ').title()} by {cat.replace('_', ' ').title()}")
                agg_mean = df.groupby(cat)[ncol].mean().reset_index().head(12)
                agg_mean.columns = [cat, ncol]
                charts[f"avg_{ncol}_by_{cat}"] = chart_engine.create_bar_chart(agg_mean, x=cat, y=ncol, title=f"Avg {ncol.replace('_', ' ').title()} by {cat.replace('_', ' ').title()}")

        # ── 7. GROUPED BAR (2 categoricals) ──────────────────────────
        if len(categorical_cols) >= 2 and numeric_cols:
            grp = df.groupby([categorical_cols[0], categorical_cols[1]])[numeric_cols[0]].sum().reset_index()
            charts["grouped_bar"] = chart_engine.create_grouped_bar(grp.head(30), x=categorical_cols[0], y=numeric_cols[0], color=categorical_cols[1], title=f"{numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0]} & {categorical_cols[1]}")

        # ── 8. PIE / DONUT CHARTS ────────────────────────────────────
        for col in categorical_cols[:3]:
            if df[col].nunique() <= 8:
                vc = df[col].value_counts().reset_index()
                vc.columns = [col, "count"]
                charts[f"donut_{col}"] = chart_engine.create_donut_chart(vc, names=col, values="count", title=f"Composition: {col.replace('_', ' ').title()}")

        # ── 9. TIME SERIES LINES ─────────────────────────────────────
        if date_cols and numeric_cols:
            dcol = date_cols[0]
            for ncol in numeric_cols[:3]:
                ts = df.groupby(dcol)[ncol].sum().reset_index().sort_values(dcol)
                charts[f"line_{ncol}"] = chart_engine.create_line_chart(ts, x=dcol, y=ncol, title=f"{ncol.replace('_', ' ').title()} Over Time")
                if len(ts) >= 10:
                    window = min(7, len(ts) // 3) or 3
                    charts[f"rolling_{ncol}"] = chart_engine.create_rolling_average_line(ts, x=dcol, y=ncol, window=window, title=f"{ncol.replace('_', ' ').title()} Trend ({window}-period Avg)")

            # Multi-line: all metrics on one chart
            if len(numeric_cols) >= 2:
                ts_all = df.groupby(dcol)[numeric_cols[:4]].sum().reset_index().sort_values(dcol)
                charts["multi_line"] = chart_engine.create_multi_line(ts_all, x=dcol, y=numeric_cols[:4], title="All Metrics Over Time")

            # Cumulative
            for ncol in numeric_cols[:2]:
                ts = df.groupby(dcol)[ncol].sum().reset_index().sort_values(dcol)
                charts[f"cumulative_{ncol}"] = chart_engine.create_cumulative_line(ts, x=dcol, y=ncol, title=f"Cumulative {ncol.replace('_', ' ').title()}")

        # ── 10. SCATTER / BUBBLE ─────────────────────────────────────
        if len(numeric_cols) >= 2:
            color = categorical_cols[0] if categorical_cols else None
            charts["scatter_xy"] = chart_engine.create_scatter_plot(df, x=numeric_cols[0], y=numeric_cols[1], color=color, title=f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()}")
        if len(numeric_cols) >= 3:
            charts["bubble_xy"] = chart_engine.create_bubble_chart(df.head(200), x=numeric_cols[0], y=numeric_cols[1], size=numeric_cols[2], color=categorical_cols[0] if categorical_cols else None, title=f"Bubble: {numeric_cols[0]} vs {numeric_cols[1]} (size={numeric_cols[2]})")

        # ── 11. VIOLIN PLOTS ─────────────────────────────────────────
        if categorical_cols:
            for col in numeric_cols[:2]:
                charts[f"violin_{col}"] = chart_engine.create_violin_plot(df, x=categorical_cols[0], y=col, title=f"{col.replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}")

        # ── 12. STACKED BAR ──────────────────────────────────────────
        if len(categorical_cols) >= 2 and numeric_cols:
            grp2 = df.groupby([categorical_cols[0], categorical_cols[1]])[numeric_cols[0]].sum().reset_index()
            charts["stacked_bar"] = chart_engine.create_stacked_bar(grp2.head(30), x=categorical_cols[0], y=numeric_cols[0], color=categorical_cols[1], title=f"Stacked: {numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0]} & {categorical_cols[1]}")

        # ── 13. CATEGORICAL HEATMAP ──────────────────────────────────
        if len(categorical_cols) >= 2 and numeric_cols:
            charts["cat_heatmap"] = chart_engine.create_categorical_heatmap(df, index_col=categorical_cols[0], columns_col=categorical_cols[1], values_col=numeric_cols[0], title=f"{numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0]} × {categorical_cols[1]}")

        # ── 14. TREEMAP ──────────────────────────────────────────────
        if len(categorical_cols) >= 2 and numeric_cols:
            agg = df.groupby(categorical_cols[:2])[numeric_cols[0]].sum().reset_index()
            charts["treemap"] = chart_engine.create_treemap(agg, path=categorical_cols[:2], values=numeric_cols[0], title=f"Treemap: {numeric_cols[0].replace('_', ' ').title()} by {' & '.join(categorical_cols[:2])}")

        # ── 15. SUNBURST ─────────────────────────────────────────────
        if len(categorical_cols) >= 2:
            counts = df.groupby(categorical_cols[:2]).size().reset_index(name="count")
            charts["sunburst"] = chart_engine.create_sunburst_chart(counts, path=categorical_cols[:2], values="count", title=f"Sunburst: {' → '.join(categorical_cols[:2])}")

        # ── 16. MISSING VALUES BAR ───────────────────────────────────
        missing = df.isnull().sum().sort_values(ascending=False)
        missing = missing[missing > 0].head(10)
        if not missing.empty:
            mdf = pd.DataFrame({"column": missing.index, "missing_count": missing.values})
            charts["missing_values"] = chart_engine.create_bar_chart(mdf, x="column", y="missing_count", title="Missing Values by Column")

        # ── 17. OVERLAID HISTOGRAMS ──────────────────────────────────
        if len(numeric_cols) >= 2:
            charts["overlaid_histograms"] = chart_engine.create_multi_histogram(df, numeric_cols[:4], title="Overlaid Distributions")

        kpis = chart_engine.generate_kpi_cards(df, numeric_cols[:4])
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
