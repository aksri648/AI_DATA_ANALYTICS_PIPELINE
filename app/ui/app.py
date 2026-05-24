import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from app.ui.sidebar import render_sidebar
from app.ui.pages.etl_pipeline import render_etl_pipeline
from app.ui.pages.analytics import render_analytics
from app.ui.pages.dashboard import render_dashboard
from app.ui.pages.data_preview import render_data_preview
from app.ui.pages.reports import render_reports
from app.ui.pages.insights import render_insights
from app.ui.pages.agent_monitor import render_agent_monitor
from app.ui.pages.settings import render_settings


st.set_page_config(
    page_title="AI Analytics & ETL Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .stSidebar { background-color: #1a1d24; }
    .stButton button { border-radius: 8px; }
    .stTextInput input { border-radius: 8px; }
    div[data-testid="stMetricValue"] { font-size: 28px; }
    .stChatMessage { border-radius: 12px; padding: 12px; }
    h1, h2, h3 { color: #f0f2f6; }
</style>
""", unsafe_allow_html=True)


def main():
    page = render_sidebar()

    pages = {
        "Data Upload & Ingestion": render_etl_pipeline,
        "ETL Pipeline": render_etl_pipeline,
        "Data Preview": render_data_preview,
        "Conversational Analytics": render_analytics,
        "Dashboards": render_dashboard,
        "AI Insights": render_insights,
        "Reports": render_reports,
        "Agent Monitor": render_agent_monitor,
        "Settings": render_settings,
    }

    render_func = pages.get(page, render_etl_pipeline)
    render_func()


if __name__ == "__main__":
    main()
