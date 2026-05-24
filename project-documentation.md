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

## Recent Changes

### SQL Identifier Quoting & Input Sanitization
- Added `quote_identifier()` in `app/db/duckdb_manager.py` for safe SQL identifier handling across all query paths (DROP, CREATE, DESCRIBE, SELECT).
- Enhanced `sanitize_table_name()` in `app/utils/helpers.py` to strip redundant underscores, handle leading digits, and fallback to `"dataset"` for empty names.
- Applied sanitization throughout ingestion, warehouse, and pipeline manager to prevent SQL injection and naming errors.

### Chart Visualization Engine (`app/charts/chart_engine.py`)
Added 10 new chart creation methods:
| Method | Description |
|--------|-------------|
| `create_violin_plot` | Violin distribution with embedded box plot |
| `create_sunburst_chart` | Hierarchical sunburst for nested categories |
| `create_treemap` | Hierarchical treemap for proportional data |
| `create_funnel_chart` | Funnel chart for conversion/pipeline stages |
| `create_waterfall_chart` | Waterfall for incremental changes |
| `create_bubble_chart` | Scatter with size dimension |
| `create_gauge_chart` | Gauge/KPI indicator with colored zones |
| `create_radar_chart` | Radar/spider chart for multi-axis comparison |
| `create_donut_chart` | Donut variant of pie chart |
| `create_stacked_bar` / `create_grouped_bar` | Stacked and grouped bar variants |
| `create_horizontal_bar` | Horizontal bar for ranked data |
| `create_multi_line` | Multiple series on a single line chart |
| `create_categorical_heatmap` | Pivot-table heatmap from two categorical + one numeric column |
| `create_missing_heatmap` | Visual missing-data pattern across rows/columns |
| `create_paired_bar` | Side-by-side bar comparison (e.g., total vs average) |
| `create_percentile_bar` | Percentile distribution bar chart |
| `create_cumulative_line` | Cumulative sum area line |
| `create_rolling_average_line` | Rolling average trend with raw scatter overlay |
| `create_multi_histogram` | Overlapping histograms for comparing distributions |

### Auto-Generated Report Charts (`generate_report_charts()`)
Given any DataFrame, `generate_report_charts()` now auto-produces **up to 51 charts** organized into sections:

| Section | Charts Generated |
|---------|-----------------|
| **Data Quality** | Completeness gauge, uniqueness gauge, missing-values bar (vertical + horizontal), missing-data pattern heatmap |
| **Bar Charts** | Value-count bars per categorical (vertical + horizontal), sum/mean aggregation bars per numeric, grouped bar, stacked bar, paired bar (sum vs mean) |
| **Line Charts & Trends** | Time-series line per date×numeric pair, rolling-average trend, cumulative total, multi-line (all metrics), line by category |
| **Heatmaps** | Correlation heatmap, categorical cross-tab (numeric values), categorical cross-tab (record counts) |
| **Distributions & Box Plots** | Histogram per numeric column, overlaid multi-histogram, percentile distribution bar, box plot per numeric, violin plot grouped by category |
| **Categorical Analysis** | Donut composition charts, sunburst hierarchy |
| **Relationships & Advanced** | Scatter (multiple pairs), bubble chart, treemap |

Chart count scales with the dataset's column types — the more numeric/categorical/date columns, the more charts are generated.

### HTML Report Redesign (`app/reports/report_generator.py`)
- Redesigned with a modern dark theme using CSS custom properties (`--bg`, `--surface`, `--accent`, etc.).
- Responsive chart grid layout (`grid-template-columns: repeat(auto-fit, minmax(500px, 1fr))`).
- Charts are automatically categorized into titled sections by the `_categorize_charts()` method.
- Styled KPI cards with hover effects, insight/recommendation lists with colored left borders.
- ETL pipeline table with status badges (`success`, `failed`, `warning`).
- Mobile-responsive breakpoints at 768px.
- Supports both `dict[str, str]` (sectioned) and `list[str]` (flat) chart inputs.

### Analytics Service & Reports Page Updates
- `AnalyticsService.process_question()` report intent now uses `generate_report_charts()` and generates recommendations via LLM.
- Reports page (`app/ui/pages/reports.py`) generates recommendations, passes chart dict to the report, and displays chart count on success.

### Dashboard Persistence (`app/db/dashboard_store.py`)
- New `DashboardStore` class backed by DuckDB (`_dashboards` table).
- Stores: dashboard name, dataset name, dashboard type, KPI JSON, chart HTML JSON, config JSON, created/updated timestamps.
- CRUD operations:
  - `save()` — upserts by name (creates new or updates existing).
  - `get_by_id()` / `get_by_name()` — loads full dashboard including cached chart HTML.
  - `list_all()` — returns metadata (id, name, dataset, type, timestamps) sorted by last updated.
  - `delete()` — removes by id.
- `DashboardBuilder.to_html_dict()` converts plotly figure objects to HTML strings for persistence.
- Dashboard UI (`app/ui/pages/dashboard.py`) now has two tabs:
  - **Build Dashboard** — generate a dashboard, then save it with a name via a form.
  - **Saved Dashboards** — list all saved dashboards, load one (renders instantly from cached HTML), or delete.
- Loaded dashboards render without re-computing data or calling the LLM.

## Recommended Next Engineering Steps
1. Add integration tests for ETL pipeline manager and MCP tool calls.
2. Add authentication/role model if multi-user local network usage is expected.
3. Add persistent artifact storage for generated dashboards/reports.
4. Add explicit SQL query sanitization middleware across all query paths.
5. Add optional FastAPI backend for API-driven automation and scheduling.
