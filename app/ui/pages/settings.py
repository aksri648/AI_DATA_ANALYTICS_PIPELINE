import streamlit as st
from app.config.settings import OLLAMA_MODEL, DUCKDB_PATH
from app.llm.ollama_service import ollama_service


def render_settings():
    st.markdown("## Settings")
    st.markdown("Configure the AI Analytics & ETL Copilot.")

    with st.expander("Ollama Configuration", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Ollama Base URL", value=ollama_service.base_url, key="ollama_url", disabled=True)
        with col2:
            st.text_input("Active Model", value=ollama_service.model, key="ollama_model", disabled=True)

        if st.button("Check Ollama Connection"):
            if ollama_service.check_health():
                st.success("Ollama is running!")
                models = ollama_service.list_models()
                st.write(f"Available models: {', '.join(models)}")
            else:
                st.error("Ollama is not running. Start it with `ollama serve`")

    with st.expander("Database Configuration", expanded=True):
        st.text_input("DuckDB Path", value=DUCKDB_PATH, disabled=True)
        st.caption("DuckDB is used as the local analytics engine.")

    with st.expander("About"):
        st.markdown("""
        **AI Analytics & ETL Copilot v1.0**

        A production-grade local AI-native ETL + Analytics platform.

        **Tech Stack:**
        - CrewAI Multi-Agent Orchestration
        - Ollama Local LLMs
        - DuckDB Analytics Engine
        - Streamlit UI
        - MCP Tools Integration

        **Agents:**
        1. Data Ingestion Agent
        2. ETL Agent
        3. SQL Analyst Agent
        4. Visualization Agent
        5. Business Insights Agent
        6. Report Generation Agent
        7. MCP Tool Agent
        8. QA Validation Agent
        """)
