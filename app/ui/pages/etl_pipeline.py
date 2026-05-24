import streamlit as st
import pandas as pd
import time
from pathlib import Path

from app.services.etl_service import etl_service
from app.db.warehouse import warehouse
from app.etl.pipeline_manager import etl_pipeline
from app.etl.profiling import DataProfiling
from app.config.settings import UPLOAD_DIR


def render_etl_pipeline():
    st.markdown("## ETL Pipeline")
    st.markdown("Automated data extraction, cleaning, transformation, and loading.")

    tab1, tab2, tab3, tab4 = st.tabs(["Ingest", "Transform", "Pipeline History", "Data Profile"])

    with tab1:
        st.markdown("### Data Ingestion")
        uploaded_file = st.file_uploader(
            "Upload a file (CSV, Excel, JSON, Parquet)",
            type=["csv", "xlsx", "xls", "json", "parquet"],
            key="etl_upload",
        )

        if uploaded_file:
            file_path = UPLOAD_DIR / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.info(f"File uploaded: {uploaded_file.name} ({uploaded_file.size:,} bytes)")

            col1, col2 = st.columns(2)
            with col1:
                table_name = st.text_input("Table name", value=Path(uploaded_file.name).stem.lower().replace(" ", "_"))
            with col2:
                run_etl = st.checkbox("Run full ETL (clean + transform + features)", value=True)

            if st.button("Ingest Data", type="primary", use_container_width=True):
                with st.status("Running ingestion pipeline...", expanded=True) as status:
                    try:
                        if run_etl:
                            result = etl_service.run_full_etl(file_path=str(file_path), name=table_name)
                        else:
                            result = etl_service.ingest_file(str(file_path), table_name)

                        st.success(f"Ingestion complete!")
                        if isinstance(result, dict):
                            st.json(result.get("metadata", result))

                        if run_etl:
                            final_table = result.get("final_table", table_name)
                            df = warehouse.get_dataset(final_table)
                            st.dataframe(df.head(20), use_container_width=True)
                            st.caption(f"Total rows: {len(df)}")

                    except Exception as e:
                        st.error(f"Ingestion failed: {e}")

    with tab2:
        st.markdown("### Transform Existing Data")
        tables = etl_service.list_datasets()
        if tables:
            selected = st.selectbox("Select dataset to transform", tables)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Auto-Clean Data", use_container_width=True):
                    with st.spinner("Cleaning data..."):
                        result = etl_service.clean_dataset(selected)
                    st.success("Cleaning complete!")
                    st.json(result.get("validation", {}))

            with col2:
                if st.button("Profile Dataset", use_container_width=True):
                    with st.spinner("Profiling data..."):
                        profile = etl_service.profile_dataset(selected)
                    st.json(profile)
        else:
            st.info("No datasets available. Ingest data first.")

    with tab3:
        st.markdown("### Pipeline History")
        history = etl_pipeline.get_pipeline_history()
        if history:
            for h in reversed(history[-20:]):
                with st.expander(f"{h['step'].title()} — {h.get('table_name', '')} ({h['timestamp']})"):
                    st.json(h)
        else:
            st.info("No pipeline runs yet.")

    with tab4:
        st.markdown("### Data Profiler")
        tables = etl_service.list_datasets()
        if tables:
            selected = st.selectbox("Select dataset to profile", tables, key="profiler_select")
            if st.button("Generate Full Profile", use_container_width=True):
                with st.spinner("Profiling..."):
                    profile = etl_service.profile_dataset(selected)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Rows", profile.get("overview", {}).get("rows", 0))
                    col2.metric("Columns", profile.get("overview", {}).get("columns", 0))
                    col3.metric("Memory", f'{profile.get("overview", {}).get("memory_mb", 0):.1f} MB')

                    if profile.get("correlation"):
                        st.subheader("Correlation Matrix")
                        corr_df = pd.DataFrame(profile["correlation"])
                        st.dataframe(corr_df, use_container_width=True)

                    if profile.get("missing_summary", {}).get("total_missing", 0) > 0:
                        st.subheader("Missing Values")
                        st.write(f"Total missing: {profile['missing_summary']['total_missing']}")
                        st.write(f"Columns with missing: {profile['missing_summary']['columns_with_missing']}")
        else:
            st.info("No datasets available.")
