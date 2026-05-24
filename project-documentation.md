# AI Analytics & ETL Copilot - Project Documentation

## Overview
- AI-native local analytics platform combining ETL, conversational BI, dashboards, reporting, CrewAI orchestration, and MCP tools.
- Runs fully on local infrastructure with Ollama for LLM inference and DuckDB as the primary analytics engine.
- UI is Streamlit-based and organized around analyst workflows: ingest -> clean/transform -> explore -> visualize -> report.

## Core Architecture
- **Frontend:** Streamlit (`app/ui/app.py`) with custom sidebar routing and dedicated feature pages.
- **Orchestration:** CrewAI agents, tasks, and crews under `app/crew/`.
- **LLM Layer:** `app/llm/ollama_service.py` wrapping Ollama model invocation, JSON parsing, model listing, health checks, embeddings.
- **Data Engine:** DuckDB (`app/db/duckdb_manager.py`) as local warehouse/query runtime; SQLAlchemy manager for external SQL sources.
- **ETL Layer:** Modular pipeline in `app/etl/` (ingestion, cleaning, transformation, validation, profiling, feature engineering).
- **Visualization Layer:** Plotly chart generation and automatic dashboard assembly in `app/charts/`.
- **Reporting Layer:** Markdown and HTML report generation in `app/reports/report_generator.py`.
- **Tooling Layer:** MCP server/client and tool registry in `app/mcp/`.

## Directory Structure (Implemented)
- `app/main.py`: main CLI launcher (`ui`, `mcp`, `check`).
- `app/config/settings.py`: centralized settings/env variables and agent definitions.
- `app/utils/`: logging and helper utilities.
- `app/llm/`: Ollama abstraction.
- `app/db/`: DuckDB + SQLAlchemy + warehouse abstraction.
- `app/etl/`: end-to-end ETL modules + pipeline manager.
- `app/charts/`: chart engine + dashboard builder.
- `app/reports/`: report generation.
- `app/mcp/`: MCP protocol server, client, and tool handlers.
- `app/crew/`: CrewAI agents, tasks, crews, tools, memory.
- `app/services/`: application-level ETL and analytics services.
- `app/ui/`: Streamlit app, sidebar, and feature pages.

## Entry Points
- Root launcher: `main.py` -> delegates to `app.main:main`.
- Modes:
  - `uv run python main.py ui` -> launches Streamlit UI.
  - `uv run python main.py mcp` -> launches MCP server (stdio).
  - `uv run python main.py check` -> validates Ollama availability/models.

## Implemented Agents (CrewAI)
- Data Ingestion Agent
- ETL Agent
- SQL Analyst Agent
- Visualization Agent
- Business Insights Agent
- Report Generation Agent
- MCP Tool Agent
- QA Validation Agent

Agent definitions are in `app/crew/agents/*.py` and configured through `AGENT_CONFIG` in `app/config/settings.py`.

## Implemented MCP Tools
- `read_excel`
- `read_csv`
- `query_sql` (read-only enforcement)
- `clean_data`
- `transform_data`
- `validate_schema`
- `profile_data`
- `generate_chart`
- `summarize_data`
- `create_dashboard`
- `generate_report`

Tools are registered in `app/mcp/tools.py` and exposed by `app/mcp/mcp_server.py`.

## ETL Workflow
1. Ingest source files (CSV/XLSX/XLS/JSON/Parquet) into DuckDB tables.
2. Auto-cleaning:
   - normalize column names
   - remove duplicates
   - drop empty rows
   - auto-fill missing values
3. Transformations:
   - dtype conversion
   - date parsing and engineered temporal features
   - optional encoding/aggregation/pivoting
4. Validation:
   - duplicate checks
   - missing value analysis
   - outlier/anomaly detection
5. Profiling:
   - descriptive stats
   - correlation matrix
   - value counts and memory stats

Primary orchestrator: `app/etl/pipeline_manager.py`.

## UI Pages
- Data Upload & Ingestion
- ETL Pipeline
- Data Preview
- Conversational Analytics
- Dashboards
- AI Insights
- Reports
- Agent Monitor
- Settings

Routing is controlled via `render_sidebar()` and page mapping in `app/ui/app.py`.

## Data & Security Controls
- Local-first design: no required cloud inference.
- SQL tool enforces read-only behavior for query execution paths.
- Environment-based configuration (`.env`) for model and runtime settings.
- File-type support is explicitly constrained via `SUPPORTED_FILE_TYPES`.

## Configuration
- Example env file: `.env.example`.
- Key variables:
  - `OLLAMA_BASE_URL`
  - `OLLAMA_MODEL`
  - `DUCKDB_PATH`
  - `STREAMLIT_PORT`
  - `MCP_SERVER_PORT`
  - `LOG_LEVEL`

## Running the Project
1. Install dependencies:
   - `uv sync`
2. Start Ollama locally:
   - `ollama serve`
   - `ollama pull qwen2.5:14b`
3. Run UI:
   - `uv run python main.py ui`
4. Optional MCP server:
   - `uv run python main.py mcp`

## Notable Implementation Details
- Streamlit default multipage sidebar is disabled via `.streamlit/config.toml` to preserve custom navigation UX.
- UI import path handling in `app/ui/app.py` includes project root insertion for reliable package imports.
- MCP server logger is configured to avoid protocol noise in stdout.

## Current Status
- Core platform components are implemented and wired.
- Modular architecture exists for production extension.
- Legacy root-level files were removed; the active implementation is fully under the `app/` package plus root `main.py` launcher.

## Recommended Next Engineering Steps
1. Add integration tests for ETL pipeline manager and MCP tool calls.
2. Add authentication/role model if multi-user local network usage is expected.
3. Add persistent artifact storage for generated dashboards/reports.
4. Add explicit SQL query sanitization middleware across all query paths.
5. Add optional FastAPI backend for API-driven automation and scheduling.
