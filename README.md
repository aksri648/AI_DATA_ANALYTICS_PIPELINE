# AI Analytics & ETL Copilot

A production-grade, fully-local AI-native ETL + Analytics platform with CrewAI multi-agent orchestration, conversational BI, automated dashboard generation, and MCP tool integration.

---

## Features

- **Multi-Agent AI System** — 8 specialized CrewAI agents working collaboratively
- **Natural Language Analytics** — Ask questions in plain English
- **Automated ETL** — Ingest, clean, transform, and validate data automatically
- **Smart Visualizations** — Auto-generated Plotly charts and dashboards
- **AI Business Insights** — Automated trend analysis and recommendations
- **Report Generation** — Downloadable HTML/Markdown reports with KPIs and charts
- **MCP Integration** — Full MCP protocol server with 11 tools
- **100% Local** — Everything runs on your machine with Ollama

## Quick Start

```bash
# Install dependencies
uv sync

# Check environment
uv run python main.py check

# Run the Streamlit UI
uv run python main.py ui

# Run the MCP server
uv run python main.py mcp
```

## Architecture

```
User → Streamlit UI → Analytics Service → CrewAI Agents → MCP Tools → DuckDB/Ollama
```

### Agents
1. **Data Ingestion Agent** — Reads files, detects schemas, loads data
2. **ETL Agent** — Cleans, transforms, validates data
3. **SQL Analyst Agent** — Generates and executes SQL queries
4. **Visualization Agent** — Creates charts and dashboards
5. **Business Insights Agent** — Extracts patterns and recommendations
6. **Report Generation Agent** — Produces formatted reports
7. **MCP Tool Agent** — Manages MCP tool execution
8. **QA Validation Agent** — Validates outputs and data quality

## MCP Server

Configure in `opencode.json`:
```json
{
  "mcpServers": {
    "ai-analytics-etl": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp.mcp_server"]
    }
  }
}
```

Available MCP tools: `read_excel`, `read_csv`, `query_sql`, `clean_data`, `transform_data`, `validate_schema`, `profile_data`, `generate_chart`, `summarize_data`, `create_dashboard`, `generate_report`

## Tech Stack

- **CrewAI** — Multi-agent orchestration
- **Ollama** — Local LLM inference
- **DuckDB** — Analytics engine
- **Streamlit** — Frontend UI
- **LangChain** — LLM integration
- **Plotly** — Interactive charts
- **SQLAlchemy** — Database connectivity
- **MCP** — Model Context Protocol

## Configuration

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```

Key settings:
- `OLLAMA_MODEL` — LLM model (default: `qwen2.5:14b`)
- `OLLAMA_BASE_URL` — Ollama server URL
- `DUCKDB_PATH` — Analytics database path

## Example Prompts

- "Upload this Excel file and analyze it"
- "Show me revenue trends over time"
- "Create a sales dashboard"
- "Why did sales drop last quarter?"
- "Generate an executive report"
- "Find anomalies in the data"
- "Compare monthly growth rates"
- "What are the top 5 products by revenue?"

## License

MIT
