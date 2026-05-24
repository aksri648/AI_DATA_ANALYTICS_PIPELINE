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
    def create_horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str = "", **kwargs) -> go.Figure:
        fig = px.bar(df, x=x, y=y, title=title, template="plotly_dark", orientation="h", **kwargs)
        fig.update_layout(yaxis=dict(autorange="reversed"))
        return fig

    @staticmethod
    def create_multi_line(df: pd.DataFrame, x: str, y: list[str], title: str = "", **kwargs) -> go.Figure:
        fig = px.line(df, x=x, y=y, title=title, template="plotly_dark", **kwargs)
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.15))
        return fig

    @staticmethod
    def create_categorical_heatmap(df: pd.DataFrame, index_col: str, columns_col: str, values_col: str,
                                   aggfunc: str = "sum", title: str = "", **kwargs) -> go.Figure:
        pivot = df.pivot_table(index=index_col, columns=columns_col, values=values_col, aggfunc=aggfunc)
        pivot = pivot.fillna(0)
        fig = px.imshow(pivot, text_auto=".0f", title=title, template="plotly_dark",
                        color_continuous_scale="Blues", aspect="auto", **kwargs)
        return fig

    @staticmethod
    def create_missing_heatmap(df: pd.DataFrame, title: str = "", max_rows: int = 50) -> go.Figure:
        subset = df.head(max_rows)
        missing = subset.isnull().astype(int)
        labels = {str(i): col for i, col in enumerate(missing.columns)}
        fig = px.imshow(
            missing.T, title=title or "Missing Data Pattern",
            template="plotly_dark", color_continuous_scale=[[0, "#1a1d29"], [1, "#EF553B"]],
            aspect="auto", labels=labels,
        )
        fig.update_layout(coloraxis_showscale=False)
        return fig

    @staticmethod
    def create_paired_bar(df: pd.DataFrame, x: str, y1: str, y2: str, title: str = "",
                          name1: str = "", name2: str = "", **kwargs) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df[x], y=df[y1], name=name1 or y1, marker_color=COLORS[0]))
        fig.add_trace(go.Bar(x=df[x], y=df[y2], name=name2 or y2, marker_color=COLORS[1]))
        fig.update_layout(barmode="group", title=title, template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_percentile_bar(df: pd.DataFrame, col: str, title: str = "", **kwargs) -> go.Figure:
        percentiles = [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
        values = df[col].quantile(percentiles).tolist()
        labels = [f"P{int(p*100)}" for p in percentiles]
        fig = go.Figure(go.Bar(
            x=labels, y=values, marker_color=COLORS[:len(labels)],
            text=[f"{v:,.1f}" for v in values], textposition="outside",
        ))
        fig.update_layout(title=title or f"Percentile Distribution: {col}", template="plotly_dark", **kwargs)
        return fig

    @staticmethod
    def create_cumulative_line(df: pd.DataFrame, x: str, y: str, title: str = "", **kwargs) -> go.Figure:
        sorted_df = df.sort_values(x).copy()
        sorted_df[f"{y}_cumulative"] = sorted_df[y].cumsum()
        fig = px.line(sorted_df, x=x, y=f"{y}_cumulative", title=title, template="plotly_dark", **kwargs)
        fig.update_traces(fill="tozeroy", line=dict(width=2))
        return fig

    @staticmethod
    def create_rolling_average_line(df: pd.DataFrame, x: str, y: str, window: int = 7,
                                    title: str = "", **kwargs) -> go.Figure:
        sorted_df = df.sort_values(x).copy()
        sorted_df[f"{y}_rolling"] = sorted_df[y].rolling(window=window, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sorted_df[x], y=sorted_df[y], mode="markers",
            name=y, marker=dict(size=3, color=COLORS[0], opacity=0.4),
        ))
        fig.add_trace(go.Scatter(
            x=sorted_df[x], y=sorted_df[f"{y}_rolling"], mode="lines",
            name=f"{window}-period Avg", line=dict(color=COLORS[1], width=2.5),
        ))
        fig.update_layout(title=title or f"{y.replace('_', ' ').title()} with {window}-Period Rolling Average",
                          template="plotly_dark", hovermode="x unified", **kwargs)
        return fig

    @staticmethod
    def create_multi_histogram(df: pd.DataFrame, cols: list[str], title: str = "", **kwargs) -> go.Figure:
        fig = go.Figure()
        for i, col in enumerate(cols):
            fig.add_trace(go.Histogram(
                x=df[col], name=col.replace("_", " ").title(),
                marker_color=COLORS[i % len(COLORS)], opacity=0.6,
            ))
        fig.update_layout(barmode="overlay", title=title or "Overlapping Distributions",
                          template="plotly_dark", **kwargs)
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

        # ── DATA QUALITY ──────────────────────────────────────────────
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

        # Missing values bar chart
        missing = df.isnull().sum().sort_values(ascending=False)
        missing = missing[missing > 0].head(15)
        if not missing.empty:
            mdf = pd.DataFrame({"column": missing.index, "missing_count": missing.values})
            charts["missing_values_bar"] = ChartEngine.create_bar_chart(
                mdf, x="column", y="missing_count", title="Missing Values by Column"
            )
            # Horizontal bar for missing values
            charts["missing_values_hbar"] = ChartEngine.create_horizontal_bar(
                mdf, x="missing_count", y="column", title="Missing Values (Horizontal)"
            )
            # Missing data pattern heatmap
            charts["missing_pattern_heatmap"] = ChartEngine.create_missing_heatmap(df, title="Missing Data Pattern")

        # ── HISTOGRAMS ────────────────────────────────────────────────
        for col in numeric_cols[:6]:
            charts[f"hist_{col}"] = ChartEngine.create_histogram(
                df, x=col, title=f"Distribution of {col.replace('_', ' ').title()}"
            )

        # Percentile bar charts for numeric columns
        for col in numeric_cols[:3]:
            charts[f"percentile_{col}"] = ChartEngine.create_percentile_bar(
                df, col, title=f"Percentile Distribution: {col.replace('_', ' ').title()}"
            )

        # Overlaid histogram if multiple numeric columns
        if len(numeric_cols) >= 2:
            charts["overlaid_histograms"] = ChartEngine.create_multi_histogram(
                df, numeric_cols[:4], title="Overlaid Distributions"
            )

        # ── BOX & VIOLIN PLOTS ────────────────────────────────────────
        for col in numeric_cols[:4]:
            charts[f"box_{col}"] = ChartEngine.create_box_plot(
                df, x=None, y=col, title=f"Box Plot: {col.replace('_', ' ').title()}"
            )

        if categorical_cols:
            for col in numeric_cols[:3]:
                charts[f"violin_{col}"] = ChartEngine.create_violin_plot(
                    df, x=categorical_cols[0], y=col,
                    title=f"{col.replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}"
                )

        # ── BAR CHARTS ────────────────────────────────────────────────
        # Value count bars for each categorical column
        for col in categorical_cols[:5]:
            vc = df[col].value_counts().head(12).reset_index()
            vc.columns = [col, "count"]
            charts[f"bar_{col}"] = ChartEngine.create_bar_chart(
                vc, x=col, y="count", title=f"Count by {col.replace('_', ' ').title()}"
            )
            charts[f"hbar_{col}"] = ChartEngine.create_horizontal_bar(
                vc, x="count", y=col, title=f"Count by {col.replace('_', ' ').title()} (Horizontal)"
            )

        # Aggregated bars: sum, mean of each numeric col grouped by first categorical
        if categorical_cols and numeric_cols:
            grp = df.groupby(categorical_cols[0])
            for ncol in numeric_cols[:3]:
                agg_sum = grp[ncol].sum().reset_index().head(15)
                agg_sum.columns = [categorical_cols[0], ncol]
                charts[f"bar_sum_{ncol}_by_{categorical_cols[0]}"] = ChartEngine.create_bar_chart(
                    agg_sum, x=categorical_cols[0], y=ncol,
                    title=f"Total {ncol.replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}"
                )
                agg_mean = grp[ncol].mean().reset_index().head(15)
                agg_mean.columns = [categorical_cols[0], ncol]
                charts[f"bar_mean_{ncol}_by_{categorical_cols[0]}"] = ChartEngine.create_bar_chart(
                    agg_mean, x=categorical_cols[0], y=ncol,
                    title=f"Average {ncol.replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}"
                )

        # Grouped bar (2 categorical + 1 numeric)
        if len(categorical_cols) >= 2 and numeric_cols:
            grp2 = df.groupby([categorical_cols[0], categorical_cols[1]])[numeric_cols[0]].sum().reset_index()
            charts["grouped_bar"] = ChartEngine.create_grouped_bar(
                grp2.head(30), x=categorical_cols[0], y=numeric_cols[0], color=categorical_cols[1],
                title=f"{numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0]} & {categorical_cols[1]}"
            )
            charts["stacked_bar"] = ChartEngine.create_stacked_bar(
                grp2.head(30), x=categorical_cols[0], y=numeric_cols[0], color=categorical_cols[1],
                title=f"Stacked: {numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0]} & {categorical_cols[1]}"
            )

        # Paired bar: compare sum vs mean for first numeric by first categorical
        if categorical_cols and numeric_cols:
            agg = df.groupby(categorical_cols[0])[numeric_cols[0]].agg(["sum", "mean"]).reset_index().head(12)
            agg.columns = [categorical_cols[0], "Total", "Average"]
            charts["paired_bar_sum_mean"] = ChartEngine.create_paired_bar(
                agg, x=categorical_cols[0], y1="Total", y2="Average",
                name1="Total", name2="Average",
                title=f"Total vs Average {numeric_cols[0].replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}"
            )

        # ── LINE CHARTS ───────────────────────────────────────────────
        # Time series: each numeric over each date column
        for dcol in date_cols[:2]:
            for ncol in numeric_cols[:3]:
                ts = df.groupby(dcol)[ncol].sum().reset_index().sort_values(dcol)
                charts[f"line_{dcol}_{ncol}"] = ChartEngine.create_line_chart(
                    ts, x=dcol, y=ncol, title=f"{ncol.replace('_', ' ').title()} Over Time"
                )
                # Rolling average
                if len(ts) >= 10:
                    window = min(7, len(ts) // 3) or 3
                    charts[f"rolling_{dcol}_{ncol}"] = ChartEngine.create_rolling_average_line(
                        ts, x=dcol, y=ncol, window=window,
                        title=f"{ncol.replace('_', ' ').title()} Trend ({window}-period Avg)"
                    )
                # Cumulative
                charts[f"cumulative_{dcol}_{ncol}"] = ChartEngine.create_cumulative_line(
                    ts, x=dcol, y=ncol,
                    title=f"Cumulative {ncol.replace('_', ' ').title()} Over Time"
                )

        # Multi-line: all numeric on one chart per date column
        if date_cols and len(numeric_cols) >= 2:
            for dcol in date_cols[:2]:
                ts = df.groupby(dcol)[numeric_cols[:4]].sum().reset_index().sort_values(dcol)
                charts[f"multiline_{dcol}"] = ChartEngine.create_multi_line(
                    ts, x=dcol, y=numeric_cols[:4],
                    title=f"All Metrics Over {dcol.replace('_', ' ').title()}"
                )

        # Line chart by category (aggregated)
        if categorical_cols and len(numeric_cols) >= 1:
            for ncol in numeric_cols[:2]:
                agg = df.groupby(categorical_cols[0])[ncol].sum().reset_index()
                charts[f"line_by_{categorical_cols[0]}_{ncol}"] = ChartEngine.create_line_chart(
                    agg, x=categorical_cols[0], y=ncol,
                    title=f"{ncol.replace('_', ' ').title()} by {categorical_cols[0].replace('_', ' ').title()}"
                )

        # ── HEATMAPS ──────────────────────────────────────────────────
        # Correlation heatmap
        if len(numeric_cols) >= 2:
            charts["correlation_heatmap"] = ChartEngine.create_heatmap(df, title="Correlation Heatmap")

        # Categorical cross-tab heatmaps
        if len(categorical_cols) >= 2 and numeric_cols:
            for ncol in numeric_cols[:2]:
                charts[f"heatmap_{categorical_cols[0]}_{categorical_cols[1]}_{ncol}"] = ChartEngine.create_categorical_heatmap(
                    df, index_col=categorical_cols[0], columns_col=categorical_cols[1], values_col=ncol,
                    title=f"{ncol.replace('_', ' ').title()} by {categorical_cols[0]} × {categorical_cols[1]}"
                )

        # Categorical × categorical count heatmap
        if len(categorical_cols) >= 2:
            cross = df.groupby([categorical_cols[0], categorical_cols[1]]).size().reset_index(name="count")
            charts[f"heatmap_counts_{categorical_cols[0]}_{categorical_cols[1]}"] = ChartEngine.create_categorical_heatmap(
                cross, index_col=categorical_cols[0], columns_col=categorical_cols[1], values_col="count",
                title=f"Record Count: {categorical_cols[0]} × {categorical_cols[1]}"
            )

        # ── DONUT / PIE ──────────────────────────────────────────────
        for col in categorical_cols[:3]:
            if df[col].nunique() <= 8:
                vc = df[col].value_counts().reset_index()
                vc.columns = [col, "count"]
                charts[f"donut_{col}"] = ChartEngine.create_donut_chart(
                    vc, names=col, values="count", title=f"Composition: {col.replace('_', ' ').title()}"
                )

        # ── SCATTER / BUBBLE ─────────────────────────────────────────
        if len(numeric_cols) >= 2:
            color = categorical_cols[0] if categorical_cols else None
            charts["scatter_xy"] = ChartEngine.create_scatter_plot(
                df, x=numeric_cols[0], y=numeric_cols[1], color=color,
                title=f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()}"
            )
            # Additional scatter pairs
            if len(numeric_cols) >= 3:
                charts["scatter_xz"] = ChartEngine.create_scatter_plot(
                    df, x=numeric_cols[0], y=numeric_cols[2], color=color,
                    title=f"{numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[2].replace('_', ' ').title()}"
                )
        if len(numeric_cols) >= 3:
            charts["bubble_xy"] = ChartEngine.create_bubble_chart(
                df.head(200), x=numeric_cols[0], y=numeric_cols[1], size=numeric_cols[2],
                color=categorical_cols[0] if categorical_cols else None,
                title=f"Bubble: {numeric_cols[0].replace('_', ' ').title()} vs {numeric_cols[1].replace('_', ' ').title()} (size={numeric_cols[2]})"
            )

        # ── TREEMAP / SUNBURST ───────────────────────────────────────
        if len(categorical_cols) >= 2 and numeric_cols:
            agg = df.groupby(categorical_cols[:2])[numeric_cols[0]].sum().reset_index()
            charts["treemap"] = ChartEngine.create_treemap(
                agg, path=categorical_cols[:2], values=numeric_cols[0],
                title=f"Treemap: {numeric_cols[0].replace('_', ' ').title()} by {' & '.join(categorical_cols[:2])}"
            )
        if len(categorical_cols) >= 2:
            counts = df.groupby(categorical_cols[:2]).size().reset_index(name="count")
            charts["sunburst"] = ChartEngine.create_sunburst_chart(
                counts, path=categorical_cols[:2], values="count",
                title=f"Sunburst: {' → '.join(categorical_cols[:2])}"
            )

        return charts


chart_engine = ChartEngine()
