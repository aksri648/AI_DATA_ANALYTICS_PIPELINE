import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any
from app.utils.logging import logger

COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]


class ChartEngine:
    @staticmethod
    def detect_chart_type(df: pd.DataFrame, user_intent: str | None = None) -> str:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        if user_intent:
            intent_map = {
                "trend": "line",
                "compare": "bar",
                "distribution": "histogram",
                "composition": "pie",
                "correlation": "scatter",
                "relationship": "scatter",
                "heatmap": "heatmap",
                "growth": "line",
                "ranking": "bar",
                "partofwhole": "pie",
            }
            for key, chart in intent_map.items():
                if key in user_intent.lower():
                    return chart

        if len(date_cols) >= 1 and len(numeric_cols) >= 1:
            return "line"
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            if df[categorical_cols[0]].nunique() <= 5 and len(numeric_cols) >= 1:
                return "pie"
            return "bar"
        if len(numeric_cols) >= 2:
            if len(numeric_cols) >= 3:
                return "scatter_matrix"
            return "scatter"
        if len(numeric_cols) >= 1:
            return "histogram"
        return "bar"

    @staticmethod
    def generate_kpi_cards(df: pd.DataFrame, metrics: list[str] | None = None) -> list[dict[str, Any]]:
        numeric_cols = metrics or df.select_dtypes(include=[np.number]).columns.tolist()[:4]
        cards = []
        for col in numeric_cols:
            cards.append({
                "title": col.replace("_", " ").title(),
                "value": f"{df[col].sum():,.2f}" if df[col].dtype in ("float64", "float32") else f"{df[col].sum():,}",
                "mean": f"{df[col].mean():,.2f}",
                "min": f"{df[col].min():,.2f}",
                "max": f"{df[col].max():,.2f}",
                "trend": "up" if df[col].iloc[-1] > df[col].iloc[0] else "down" if len(df) > 1 else "neutral",
            })
        return cards

    @staticmethod
    def create_line_chart(df: pd.DataFrame, x: str, y: str | list[str], title: str = "", **kwargs) -> go.Figure:
        fig = px.line(df, x=x, y=y, title=title, template="plotly_dark", **kwargs)
        fig.update_layout(hovermode="x unified")
        return fig

    @staticmethod
    def create_bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.bar(df, x=x, y=y, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_pie_chart(df: pd.DataFrame, names: str, values: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.pie(df, names=names, values=values, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_scatter_plot(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "", **kwargs) -> go.Figure:
        fig = px.scatter(df, x=x, y=y, color=color, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_histogram(df: pd.DataFrame, x: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.histogram(df, x=x, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_heatmap(df: pd.DataFrame, title: str = "", **kwargs) -> go.Figure:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] < 2:
            return None
        corr = numeric.corr()
        fig = px.imshow(corr, text_auto=True, title=title or "Correlation Heatmap", template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_area_chart(df: pd.DataFrame, x: str, y: str | list[str], title: str = "", **kwargs) -> go.Figure:
        fig = px.area(df, x=x, y=y, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_box_plot(df: pd.DataFrame, x: str | None, y: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.box(df, x=x, y=y, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_violin_plot(df: pd.DataFrame, x: str | None, y: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.violin(df, x=x, y=y, title=title, template="plotly_dark", box=True, **kwargs)
        return fig

    @staticmethod
    def create_sunburst_chart(df: pd.DataFrame, path: list[str], values: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.sunburst(df, path=path, values=values, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_treemap(df: pd.DataFrame, path: list[str], values: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.treemap(df, path=path, values=values, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_funnel_chart(df: pd.DataFrame, x: str, y: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.funnel(df, x=x, y=y, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_waterfall_chart(df: pd.DataFrame, x: str, y: str, title: str = "", **kwargs) -> go.Figure:
        fig = go.Figure(go.Waterfall(
            x=df[x].tolist(),
            y=df[y].tolist(),
            connector={"line": {"color": "#888"}},
            increasing={"marker": {"color": "#00CC96"}},
            decreasing={"marker": {"color": "#EF553B"}},
        ))
        fig.update_layout(title=title, template="plotly_dark")
        return fig

    @staticmethod
    def create_bubble_chart(df: pd.DataFrame, x: str, y: str, size: str, color: str | None = None, title: str = "", **kwargs) -> go.Figure:
        fig = px.scatter(df, x=x, y=y, size=size, color=color, title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_gauge_chart(value: float, title: str = "", max_val: float = 100, suffix: str = "") -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title, "font": {"size": 16}},
            number={"suffix": suffix},
            gauge={
                "axis": {"range": [0, max_val]},
                "bar": {"color": "#636EFA"},
                "steps": [
                    {"range": [0, max_val * 0.3], "color": "#EF553B"},
                    {"range": [max_val * 0.3, max_val * 0.7], "color": "#FFA15A"},
                    {"range": [max_val * 0.7, max_val], "color": "#00CC96"},
                ],
            },
        ))
        fig.update_layout(template="plotly_dark", height=250, margin=dict(t=50, b=10, l=30, r=30))
        return fig

    @staticmethod
    def create_radar_chart(categories: list[str], values: list[float], title: str = "") -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            line=dict(color="#636EFA"),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title=title, template="plotly_dark",
        )
        return fig

    @staticmethod
    def create_donut_chart(df: pd.DataFrame, names: str, values: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.pie(df, names=names, values=values, title=title, template="plotly_dark", hole=0.4, **kwargs)
        return fig

    @staticmethod
    def create_stacked_bar(df: pd.DataFrame, x: str, y: str, color: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.bar(df, x=x, y=y, color=color, title=title, template="plotly_dark", barmode="stack", **kwargs)
        return fig

    @staticmethod
    def create_grouped_bar(df: pd.DataFrame, x: str, y: str, color: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.bar(df, x=x, y=y, color=color, title=title, template="plotly_dark", barmode="group", **kwargs)
        return fig

    @staticmethod
    def auto_chart(df: pd.DataFrame, user_intent: str | None = None, **kwargs) -> go.Figure:
        chart_type = ChartEngine.detect_chart_type(df, user_intent)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        try:
            if chart_type == "line" and date_cols and numeric_cols:
                return ChartEngine.create_line_chart(df, x=date_cols[0], y=numeric_cols[0], **kwargs)
            elif chart_type == "pie" and categorical_cols and numeric_cols:
                top = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index().head(10)
                return ChartEngine.create_pie_chart(top, names=categorical_cols[0], values=numeric_cols[0], **kwargs)
            elif chart_type == "scatter" and len(numeric_cols) >= 2:
                color = categorical_cols[0] if categorical_cols else None
                return ChartEngine.create_scatter_plot(df, x=numeric_cols[0], y=numeric_cols[1], color=color, **kwargs)
            elif chart_type == "histogram" and numeric_cols:
                return ChartEngine.create_histogram(df, x=numeric_cols[0], **kwargs)
            elif chart_type == "heatmap":
                heatmap = ChartEngine.create_heatmap(df, **kwargs)
                if heatmap:
                    return heatmap
            elif chart_type == "bar" and categorical_cols and numeric_cols:
                top = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().reset_index().head(20)
                return ChartEngine.create_bar_chart(top, x=categorical_cols[0], y=numeric_cols[0], **kwargs)
        except Exception as e:
            logger.warning(f"Auto chart failed: {e}")

        if numeric_cols:
            return ChartEngine.create_histogram(df, x=numeric_cols[0], **kwargs)
        return ChartEngine.create_bar_chart(df, x=df.columns[0], y=df.columns[1] if len(df.columns) > 1 else None)

    @staticmethod
    def figure_to_html(fig: go.Figure) -> str:
        return fig.to_html(include_plotlyjs="cdn", full_html=False)

    @staticmethod
    def generate_report_charts(df: pd.DataFrame) -> dict[str, Any]:
        """Generate a comprehensive set of charts for an HTML report based on data analysis."""
        charts: dict[str, go.Figure] = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        # 1. Overview / Data Quality Gauges
        total_cells = len(df) * len(df.columns)
        missing_cells = int(df.isnull().sum().sum())
        completeness = round(((total_cells - missing_cells) / total_cells) * 100, 1) if total_cells else 0
        duplicate_pct = round(df.duplicated().sum() / len(df) * 100, 1) if len(df) > 0 else 0
        charts["quality_completeness"] = ChartEngine.create_gauge_chart(
            completeness, title="Data Completeness %", suffix="%"
        )
        charts["quality_duplicates"] = ChartEngine.create_gauge_chart(
            100 - duplicate_pct, title="Uniqueness %", suffix="%"
        )

        # 2. Missing Values Bar
        missing = df.isnull().sum().sort_values(ascending=False)
        missing = missing[missing > 0].head(15)
        if not missing.empty:
            mdf = pd.DataFrame({"column": missing.index, "missing_count": missing.values})
            charts["missing_values"] = ChartEngine.create_bar_chart(
                mdf, x="column", y="missing_count", title="Missing Values by Column"
            )

        # 3. Numeric Distributions (histograms for up to 6 numeric cols)
        for col in numeric_cols[:6]:
            key = f"hist_{col}"
            charts[key] = ChartEngine.create_histogram(df, x=col, title=f"Distribution of {col.replace('_', ' ').title()}")

        # 4. Box Plots (up to 4 numeric cols)
        for col in numeric_cols[:4]:
            key = f"box_{col}"
            charts[key] = ChartEngine.create_box_plot(df, x=None, y=col, title=f"Box Plot: {col.replace('_', ' ').title()}")

        # 5. Correlation Heatmap
        if len(numeric_cols) >= 2:
            charts["correlation_heatmap"] = ChartEngine.create_heatmap(df, title="Correlation Heatmap")

        # 6. Categorical Top-N Bar Charts (up to 4)
        for col in categorical_cols[:4]:
            vc = df[col].value_counts().head(10).reset_index()
            vc.columns = [col, "count"]
            key = f"cat_{col}"
            charts[key] = ChartEngine.create_bar_chart(
                vc, x=col, y="count", title=f"Top Values: {col.replace('_', ' ').title()}"
            )

        # 7. Categorical Donut Charts (up to 3, only if <=8 unique values)
        for col in categorical_cols[:3]:
            if df[col].nunique() <= 8:
                vc = df[col].value_counts().reset_index()
                vc.columns = [col, "count"]
                key = f"donut_{col}"
                charts[key] = ChartEngine.create_donut_chart(
                    vc, names=col, values="count", title=f"Composition: {col.replace('_', ' ').title()}"
                )

        # 8. Time Series Lines (date + numeric pairs)
        for dcol in date_cols[:2]:
            for ncol in numeric_cols[:2]:
                ts = df.groupby(dcol)[ncol].sum().reset_index().sort_values(dcol)
                key = f"timeseries_{dcol}_{ncol}"
                charts[key] = ChartEngine.create_line_chart(
                    ts, x=dcol, y=ncol, title=f"{ncol.replace('_', ' ').title()} Over Time"
                )

        # 9. Scatter / Bubble (if >=2 numeric)
        if len(numeric_cols) >= 2:
            color = categorical_cols[0] if categorical_cols else None
            charts["scatter_xy"] = ChartEngine.create_scatter_plot(
                df, x=numeric_cols[0], y=numeric_cols[1], color=color,
                title=f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()}"
            )
        if len(numeric_cols) >= 3:
            size_col = numeric_cols[2]
            charts["bubble_xy"] = ChartEngine.create_bubble_chart(
                df.head(200), x=numeric_cols[0], y=numeric_cols[1], size=size_col,
                color=categorical_cols[0] if categorical_cols else None,
                title=f"Bubble: {numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()} (size={size_col})"
            )

        # 10. Violin Plots (up to 2 numeric cols, grouped by first categorical)
        if categorical_cols:
            for col in numeric_cols[:2]:
                key = f"violin_{col}"
                charts[key] = ChartEngine.create_violin_plot(
                    df, x=categorical_cols[0], y=col,
                    title=f"{col.replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}"
                )

        # 11. Stacked Bar (categorical vs numeric, colored by 2nd categorical)
        if len(categorical_cols) >= 2 and numeric_cols:
            grp = df.groupby([categorical_cols[0], categorical_cols[1]])[numeric_cols[0]].sum().reset_index()
            charts["stacked_bar"] = ChartEngine.create_stacked_bar(
                grp.head(50), x=categorical_cols[0], y=numeric_cols[0], color=categorical_cols[1],
                title=f"{numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0]} and {categorical_cols[1]}"
            )

        # 12. Treemap (if >=2 categorical + 1 numeric)
        if len(categorical_cols) >= 2 and numeric_cols:
            agg = df.groupby(categorical_cols[:2])[numeric_cols[0]].sum().reset_index()
            charts["treemap"] = ChartEngine.create_treemap(
                agg, path=categorical_cols[:2], values=numeric_cols[0],
                title=f"Treemap: {numeric_cols[0].replace('_', ' ').title()} by {' & '.join(categorical_cols[:2])}"
            )

        return charts


chart_engine = ChartEngine()
