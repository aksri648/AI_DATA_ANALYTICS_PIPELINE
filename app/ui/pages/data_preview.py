import streamlit as st
import pandas as pd
from app.db.warehouse import warehouse
from app.etl.validation import DataValidation
from app.etl.profiling import DataProfiling


def render_data_preview():
    st.markdown("## Data Preview")
    st.markdown("Browse and inspect loaded datasets.")

    tables = warehouse.list_datasets()
    if not tables:
        st.info("No datasets available. Upload data first.")
        return

    selected = st.selectbox("Select a dataset to view", tables, key="preview_select")

    if selected:
        df = warehouse.get_dataset(selected)

        tab1, tab2, tab3, tab4 = st.tabs(["Preview", "Schema", "Statistics", "Quality Report"])

        with tab1:
            st.dataframe(df, use_container_width=True)
            st.caption(f"Rows: {len(df):,} | Columns: {len(df.columns)}")

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download as CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name=f"{selected}.csv",
                    mime="text/csv",
                )
            with col2:
                st.download_button(
                    "Download as JSON",
                    data=df.to_json(orient="records").encode("utf-8"),
                    file_name=f"{selected}.json",
                    mime="application/json",
                )

        with tab2:
            st.subheader("Column Details")
            schema = DataProfiling.value_counts_profile(df)
            for col, info in schema.items():
                with st.expander(f"{col} — {info['dtype']} ({info['unique']} unique)"):
                    st.json(info.get("top_values", {}))

        with tab3:
            st.subheader("Descriptive Statistics")
            stats = DataProfiling.descriptive_stats(df)
            if not stats.empty:
                st.dataframe(stats, use_container_width=True)
            else:
                st.info("No numeric columns to compute statistics.")

            st.subheader("Missing Values")
            missing = DataProfiling.missing_patterns(df)
            if not missing.empty:
                st.dataframe(missing, use_container_width=True)
            else:
                st.info("No missing values found.")

        with tab4:
            st.subheader("Data Quality Report")
            validation = DataValidation.validate_dataset(df)
            st.json(validation)
