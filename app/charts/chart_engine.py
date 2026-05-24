import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any
from app.utils.logging import logger


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


chart_engine = ChartEngine()
