import streamlit as st
from app.reports.report_generator import report_generator
from app.charts.chart_engine import chart_engine
from app.charts.dashboard_builder import dashboard_builder
from app.etl.profiling import DataProfiling
from app.etl.validation import DataValidation
from app.etl.pipeline_manager import etl_pipeline
from app.db.warehouse import warehouse
from app.llm.ollama_service import ollama_service


def render_reports():
    st.markdown("## Reports")
    st.markdown("Generate and download analytics reports.")

    tables = warehouse.list_datasets()
    if not tables:
        st.info("No datasets available. Upload data first.")
        return

    col1, col2 = st.columns(2)
    with col1:
        selected = st.selectbox("Dataset", tables)
    with col2:
        report_title = st.text_input("Report Title", value="Analytics Report")
    report_format = st.selectbox("Format", ["markdown", "html"])

    if st.button("Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating comprehensive report..."):
            try:
                df = warehouse.get_dataset(selected)
                profile = DataProfiling.full_profile(df)
                validation = DataValidation.validate_dataset(df)
                kpis = chart_engine.generate_kpi_cards(df)
                dashboard = dashboard_builder.auto_dashboard(df)
                history = etl_pipeline.get_pipeline_history()

                prompt = f"""Generate an executive summary for a dataset with:
- {profile.get('overview', {}).get('rows', 0)} rows, {profile.get('overview', {}).get('columns', 0)} columns
- {profile.get('overview', {}).get('duplicate_pct', 0)}% duplicates
- Key columns: {list(profile.get('column_types', {}).keys())[:5]}

Write a professional 2-3 paragraph executive summary."""
                summary = ollama_service.invoke(prompt)

                insights_prompt = f"""Based on this data profile, list 5 specific business insights:
Profile: {profile}
Validation: {validation}"""
                insights_text = ollama_service.invoke(insights_prompt)
                insights = [l for l in insights_text.split("\n") if l.strip() and not l.startswith("#")][:5]

                charts_html = []
                for fig in dashboard.get("charts", {}).values():
                    if fig:
                        charts_html.append(fig.to_html(include_plotlyjs="cdn", full_html=False))

                if report_format == "html":
                    report = report_generator.generate_html_report(
                        report_title, summary, kpis, insights, charts_html, history
                    )
                    st.download_button(
                        "Download HTML Report",
                        data=report.encode("utf-8"),
                        file_name=f"{report_title.lower().replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                    st.components.v1.html(report, height=600, scrolling=True)
                else:
                    report = report_generator.generate_markdown_report(
                        report_title, summary, kpis, insights, charts_html, history
                    )
                    st.download_button(
                        "Download Markdown Report",
                        data=report.encode("utf-8"),
                        file_name=f"{report_title.lower().replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                    st.markdown(report)

                st.success("Report generated successfully!")

            except Exception as e:
                st.error(f"Report generation failed: {e}")

    with st.expander("Example Prompts"):
        st.markdown("""
        - "Create a sales dashboard for revenue trends"
        - "Analyze customer churn patterns"
        - "Generate executive summary of financial data"
        - "Show me top-performing products"
        - "Compare quarterly growth rates"
        """)
