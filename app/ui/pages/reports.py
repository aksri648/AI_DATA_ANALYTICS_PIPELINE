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
    st.markdown("Generate comprehensive analytics reports with rich visualizations.")

    tables = warehouse.list_datasets()
    if not tables:
        st.info("No datasets available. Upload data first.")
        return

    col1, col2 = st.columns(2)
    with col1:
        selected = st.selectbox("Dataset", tables)
    with col2:
        report_title = st.text_input("Report Title", value="Analytics Report")
    report_format = st.selectbox("Format", ["html", "markdown"])

    if st.button("Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating comprehensive report with visualizations..."):
            try:
                df = warehouse.get_dataset(selected)
                profile = DataProfiling.full_profile(df)
                validation = DataValidation.validate_dataset(df)
                kpis = chart_engine.generate_kpi_cards(df)
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

                recommendations_prompt = f"""Based on this data profile, provide 5 actionable recommendations:
Profile: {profile}
Insights: {insights}"""
                recs_text = ollama_service.invoke(recommendations_prompt)
                recommendations = [l for l in recs_text.split("\n") if l.strip() and not l.startswith("#")][:5]

                report_figures = chart_engine.generate_report_charts(df)
                charts_html = {}
                for name, fig in report_figures.items():
                    if fig is not None:
                        charts_html[name] = chart_engine.figure_to_html(fig)

                if report_format == "html":
                    report = report_generator.generate_html_report(
                        report_title, summary, kpis, insights, charts_html, history, recommendations
                    )
                    st.download_button(
                        "Download HTML Report",
                        data=report.encode("utf-8"),
                        file_name=f"{report_title.lower().replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                    st.components.v1.html(report, height=900, scrolling=True)
                else:
                    all_charts_flat = list(charts_html.values())
                    report = report_generator.generate_markdown_report(
                        report_title, summary, kpis, insights, all_charts_flat, history, recommendations
                    )
                    st.download_button(
                        "Download Markdown Report",
                        data=report.encode("utf-8"),
                        file_name=f"{report_title.lower().replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                    st.markdown(report)

                st.success(f"Report generated successfully with {len(charts_html)} visualizations!")

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
