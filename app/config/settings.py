import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = BASE_DIR / "app"
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "2048"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.0"))
OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.9"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

DUCKDB_PATH = os.getenv("DUCKDB_PATH", str(BASE_DIR / "analytics.duckdb"))

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "warehouse.db"))

CREWAI_VERBOSE = os.getenv("CREWAI_VERBOSE", "true").lower() == "true"
CREWAI_MAX_RPM = int(os.getenv("CREWAI_MAX_RPM", "10"))

STREAMLIT_THEME = os.getenv("STREAMLIT_THEME", "dark")
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))

MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "9000"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))

SUPPORTED_DB_TYPES = ["sqlite", "postgresql", "mysql", "mssql"]

SUPPORTED_FILE_TYPES = {
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".json": "application/json",
    ".parquet": "application/octet-stream",
    ".pdf": "application/pdf",
}

DEFAULT_CHART_THEME = "plotly_dark"

AGENT_CONFIG = {
    "ingestion": {
        "name": "Data Ingestion Specialist",
        "role": "Data Ingestion Agent",
        "goal": "Efficiently ingest data from files and databases",
        "backstory": "Expert in data extraction and schema detection",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "etl": {
        "name": "ETL Engineer",
        "role": "ETL Agent",
        "goal": "Clean, transform, and validate data pipelines",
        "backstory": "Senior data engineer specializing in data quality",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "sql_analyst": {
        "name": "SQL Analyst",
        "role": "SQL Analyst Agent",
        "goal": "Generate and optimize analytical SQL queries",
        "backstory": "Expert SQL analyst with deep database knowledge",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "visualization": {
        "name": "Visualization Designer",
        "role": "Visualization Agent",
        "goal": "Create beautiful interactive charts and dashboards",
        "backstory": "Expert data visualization designer",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "insights": {
        "name": "Business Insights Analyst",
        "role": "Business Insights Agent",
        "goal": "Extract actionable business insights from data",
        "backstory": "Senior business intelligence analyst",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "report": {
        "name": "Report Generator",
        "role": "Report Generation Agent",
        "goal": "Generate comprehensive analytical reports",
        "backstory": "Expert technical writer and data storyteller",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "mcp_tool": {
        "name": "MCP Tool Manager",
        "role": "MCP Tool Agent",
        "goal": "Manage and execute MCP tool operations",
        "backstory": "Expert in MCP protocol and tool orchestration",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
    "qa": {
        "name": "Quality Assurance Analyst",
        "role": "QA Validation Agent",
        "goal": "Validate all outputs for quality and accuracy",
        "backstory": "Senior QA engineer with data validation expertise",
        "allow_delegation": False,
        "verbose": CREWAI_VERBOSE,
    },
}
