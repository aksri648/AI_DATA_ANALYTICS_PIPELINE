import streamlit as st
from app.llm.ollama_service import ollama_service
from app.db.warehouse import warehouse
from app.etl.profiling import DataProfiling
from app.etl.validation import DataValidation
from app.charts.chart_engine import chart_engine


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
                cols = st.columns(len(kpis))
                for i, kpi in enumerate(kpis):
                    cols[i].metric(kpi.get("title", ""), kpi.get("value", ""))

                prompt = f"""You are a senior business intelligence analyst. Analyze this dataset and provide:

1. **Executive Summary** (2-3 sentences)
2. **Key Trends & Patterns** (3-5 bullet points)
3. **Anomalies & Outliers** (list any unusual findings)
4. **Business Recommendations** (3-5 actionable recommendations)

Dataset Profile:
{profile}

Data Validation:
{validation}

Key KPIs:
{kpis}"""

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
