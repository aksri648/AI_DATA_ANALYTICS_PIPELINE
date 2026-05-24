import streamlit as st
from typing import Any

from app.db.warehouse import warehouse
from app.llm.ollama_service import ollama_service
from app.config.settings import OLLAMA_MODEL


def render_sidebar() -> str:
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
        st.markdown("## AI Analytics Copilot")
        st.divider()

        page = st.radio(
            "Navigation",
            options=[
                "Data Upload & Ingestion",
                "ETL Pipeline",
                "Data Preview",
                "Conversational Analytics",
                "Dashboards",
                "AI Insights",
                "Reports",
                "Agent Monitor",
                "Settings",
            ],
            index=0,
            label_visibility="collapsed",
        )
        st.divider()

        with st.expander("System Status", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                ollama_ok = ollama_service.check_health()
                st.markdown(f"**Ollama:** {'✅' if ollama_ok else '❌'}")
            with col2:
                datasets = warehouse.list_datasets()
                st.markdown(f"**Datasets:** {len(datasets)}")

            if ollama_ok:
                model = st.selectbox(
                    "Active Model",
                    options=ollama_service.list_models() or [OLLAMA_MODEL],
                    index=0,
                )
                if model != ollama_service.model:
                    ollama_service.set_model(model)
                    st.rerun()

        with st.expander("Available Datasets", expanded=False):
            tables = warehouse.list_datasets()
            if tables:
                for t in tables:
                    st.markdown(f"- `{t}`")
            else:
                st.info("No datasets loaded yet")

        st.divider()
        st.caption("AI Analytics & ETL Copilot v1.0")
        st.caption("Powered by CrewAI + Ollama + DuckDB")

    return page
