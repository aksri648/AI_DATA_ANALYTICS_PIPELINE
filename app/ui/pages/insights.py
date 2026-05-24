import streamlit as st
from app.llm.ollama_service import ollama_service
from app.db.warehouse import warehouse
from app.etl.profiling import DataProfiling
from app.etl.validation import DataValidation
from app.charts.chart_engine import chart_engine


def _build_data_context(df, profile, validation) -> str:
    """Build a rich data context string with actual values for the LLM."""
    import numpy as np

    parts = []

    # Shape
    parts.append(f"DATASET: {len(df)} rows × {len(df.columns)} columns")
    parts.append(f"COLUMNS: {', '.join(df.columns.tolist())}")
    parts.append("")

    # First 5 rows as CSV-like
    parts.append("SAMPLE ROWS (first 5):")
    parts.append(df.head(5).to_string(index=False))
    parts.append("")

    # Numeric summary with actual stats
    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        parts.append("NUMERIC COLUMNS SUMMARY:")
        desc = numeric.describe().T
        desc["missing"] = numeric.isnull().sum()
        desc["unique"] = numeric.nunique()
        for col in desc.index:
            row = desc.loc[col]
            parts.append(
                f"  {col}: mean={row['mean']:.2f}, median={row['50%']:.2f}, "
                f"min={row['min']:.2f}, max={row['max']:.2f}, "
                f"std={row['std']:.2f}, missing={int(row['missing'])}, unique={int(row['unique'])}"
            )
        parts.append("")

    # Categorical column value counts
    categorical = df.select_dtypes(include=["object", "category"])
    if not categorical.empty:
        parts.append("CATEGORICAL COLUMNS DISTRIBUTION:")
        for col in categorical.columns[:8]:
            vc = df[col].value_counts()
            top_vals = ", ".join(f"{k}={v}" for k, v in vc.head(8).items())
            parts.append(f"  {col} ({df[col].nunique()} unique): {top_vals}")
        parts.append("")

    # Key correlations
    if len(numeric.columns) >= 2:
        corr = numeric.corr()
        pairs = []
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                val = corr.iloc[i, j]
                if abs(val) > 0.3:
                    pairs.append((corr.columns[i], corr.columns[j], val))
        if pairs:
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            parts.append("NOTABLE CORRELATIONS:")
            for c1, c2, v in pairs[:10]:
                parts.append(f"  {c1} ↔ {c2}: {v:.3f}")
            parts.append("")

    # Group-by summaries for key categorical × numeric
    if not categorical.empty and not numeric.empty:
        cat_col = categorical.columns[0]
        parts.append(f"GROUP-BY ANALYSIS (by {cat_col}):")
        for ncol in numeric.columns[:4]:
            grp = df.groupby(cat_col)[ncol].agg(["mean", "sum", "count"]).round(2)
            for idx in grp.index:
                row = grp.loc[idx]
                parts.append(f"  {cat_col}={idx}: avg_{ncol}={row['mean']}, total_{ncol}={row['sum']}, count={int(row['count'])}")
        parts.append("")

    # Outlier info
    if validation and validation.get("outliers"):
        outlier_cols = validation["outliers"]
        if isinstance(outlier_cols, dict):
            parts.append("OUTLIERS DETECTED:")
            for col, info in outlier_cols.items():
                if isinstance(info, dict) and info.get("count", 0) > 0:
                    parts.append(f"  {col}: {info['count']} outliers ({info.get('percentage', 0):.1f}%)")
            parts.append("")

    return "\n".join(parts)


def render_insights():
    st.markdown("## AI Business Insights")
    st.markdown("Automatically generated insights from your data.")

    tables = warehouse.list_datasets()
    if not tables:
        st.info("No datasets available. Upload data first.")
        return

    selected = st.selectbox("Select dataset for analysis", tables)

    if st.button("Generate Insights", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing your data..."):
            try:
                df = warehouse.get_dataset(selected)
                profile = DataProfiling.full_profile(df)
                validation = DataValidation.validate_dataset(df)
                kpis = chart_engine.generate_kpi_cards(df)

                st.subheader("Key Metrics")
                cols = st.columns(min(len(kpis), 4))
                for i, kpi in enumerate(kpis[:4]):
                    cols[i].metric(kpi.get("title", ""), kpi.get("value", ""))

                data_context = _build_data_context(df, profile, validation)

                prompt = f"""You are a senior business intelligence analyst. Below is a real dataset. Analyze the ACTUAL DATA VALUES and provide genuine business insights — not descriptions of the data structure.

{data_context}

Provide your analysis in this format:

## Executive Summary
2-3 sentences describing the most important findings from the actual data.

## Key Findings
- List 5-8 specific findings based on the actual values, distributions, and patterns you see above.
- Reference real numbers, percentages, and comparisons.
- Focus on what the data MEANS for the business, not what columns exist.

## Trends & Patterns
- Identify 3-5 meaningful patterns in the data.
- Note any correlations, seasonal effects, or group differences.
- Use specific values from the data.

## Anomalies & Concerns
- Flag any data quality issues or unusual values that need attention.
- Identify outliers or unexpected patterns.

## Actionable Recommendations
- Provide 3-5 concrete, data-backed recommendations.
- Each recommendation should reference specific findings from the data.
- Focus on what actions the business should take.

IMPORTANT: Do NOT describe the dataset structure, column names, or data types. Analyze the actual VALUES and derive business conclusions."""

                analysis = ollama_service.invoke(prompt)
                st.markdown(analysis)

                st.download_button(
                    "Download Insights",
                    data=analysis.encode("utf-8"),
                    file_name=f"{selected}_insights.md",
                    mime="text/markdown",
                )

            except Exception as e:
                st.error(f"Insight generation failed: {e}")
