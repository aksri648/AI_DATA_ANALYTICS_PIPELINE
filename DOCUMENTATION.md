# AI Data Analyst 2.0 — Documentation

A natural language to SQL query system that converts plain English questions into executable SQL against any SQLAlchemy-supported database. Powered by LangChain and local Ollama LLMs.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Module Reference](#module-reference)
  - [main.py — Core Engine](#mainpy--core-engine)
  - [frontend.py — Streamlit UI](#frontendpy--streamlit-ui)
  - [create_database.py — Database Bootstrap](#create_databasepy--database-bootstrap)
  - [db_mcp_server.py — MCP Database Creation Tool](#db_mcp_serverpy--mcp-database-creation-tool)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [MCP Server](#mcp-server)
- [Model Configuration](#model-configuration)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## Overview

AI Data Analyst 2.0 bridges the gap between natural language and structured data. Users ask questions in plain English (e.g., *"Show me the top 5 products by revenue"*) and receive query results without writing a single line of SQL.

The system follows a three-step pipeline:

1. **Schema Extraction** — Introspects any SQLAlchemy-compatible database to discover tables and columns.
2. **Text-to-SQL Generation** — Sends the schema + user question to a local LLM via Ollama, which returns a SQL query.
3. **Query Execution** — Runs the generated SQL against the database and returns results.

The project also includes an **MCP server** that exposes a `create_database` tool, allowing you to create SQLite databases from natural language descriptions (e.g., *"create a CRM database with contacts and deals tables"*).

---

## Architecture

```
User Question (natural language)
         │
         ▼
┌─────────────────────────┐
│  extract_schema(db_url) │  ← SQLAlchemy inspector
│  returns JSON           │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────┐
│  text_to_sql()      │  ← LangChain prompt template + OllamaLLM
│  returns SQL string │
└─────────┬───────────┘
          │
          ▼
┌──────────────────────────┐
│get_data_from_database()  │  ← SQLAlchemy text() execution
│  returns list[tuple]     │
└─────────┬────────────────┘
          │
          ▼
    Query Results


MCP Server (separate process via stdio):
┌──────────────────────┐
│  db_mcp_server.py    │
│  └─ create_database  │  ← JSON-RPC over stdio
│     tool             │
└──────────────────────┘
```

`get_data_from_database()` now accepts any SQLAlchemy database URL, making it compatible with SQLite, PostgreSQL, MySQL, and more.

---

## Tech Stack

| Component        | Technology                                      |
|------------------|-------------------------------------------------|
| Language         | Python 3.11+                                    |
| Database         | SQLite, PostgreSQL, MySQL (any SQLAlchemy DB)   |
| ORM / Introspect | SQLAlchemy 2.x (inspect engine + text execution) |
| LLM Framework    | LangChain Core + LangChain Ollama               |
| LLM Backend      | Ollama (local) — default: `deepseek-r1:8b`     |
| Frontend         | Streamlit (connection-first UI)                 |
| MCP Protocol     | JSON-RPC 2.0 over stdio                         |
| Package Manager  | `uv` (Astral)                                   |

---

## Project Structure

```
ai-data-analyst-2-main/
├── amazon.db             # SQLite database (pre-populated with sample data)
├── create_database.py    # Script to bootstrap the database with tables + dummy data
├── main.py               # Core engine: schema extraction, text-to-SQL, query execution
├── frontend.py           # Streamlit web UI with connection-first workflow
├── db_mcp_server.py      # MCP server exposing create_database tool
├── pyproject.toml        # Project metadata and Python dependencies
├── uv.lock               # Lockfile for deterministic dependency resolution
├── README.md             # Quick-start guide
└── DOCUMENTATION.md      # Full project documentation
```

---

## Setup & Installation

### Prerequisites

- **Python 3.11+**
- **Ollama** installed and running ([ollama.com/download](https://ollama.com/download))
- A local LLM pulled into Ollama (see [Model Configuration](#model-configuration))

### Install `uv` (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Dependencies

```bash
uv sync
```

This reads `pyproject.toml`, resolves all dependencies, and creates a virtual environment automatically.

### Create the Sample Database

```bash
uv run python create_database.py
```

This creates `amazon.db` with four tables (`customers`, `products`, `orders`, `order_items`) and sample data.

### Run the Application

**CLI / Python API:**
```bash
uv run python -c "from main import get_data_from_database; print(get_data_from_database('Show all products'))"
```

**Streamlit UI:**
```bash
uv run streamlit run frontend.py
```

**MCP Server:**
```bash
uv run python db_mcp_server.py
```

---

## Module Reference

### `main.py` — Core Engine

The central module containing all pipeline logic. Refactored to accept any SQLAlchemy-compatible database URL.

#### `extract_schema(db_url: str) -> str`

Uses SQLAlchemy's `inspect` to extract table and column names from any database. Returns a JSON string like:

```json
{
  "customers": ["customer_id", "name", "email", "city", "join_date"],
  "products": ["product_id", "name", "category", "price"],
  "orders": ["order_id", "customer_id", "order_date", "total_amount"],
  "order_items": ["order_item_id", "order_id", "product_id", "quantity", "subtotal"]
}
```

**Parameters:**
| Name    | Type   | Description                  |
|---------|--------|------------------------------|
| db_url  | str    | SQLAlchemy database URL (e.g., `sqlite:///amazon.db`, `postgresql://user:pass@host/db`) |

**Returns:** JSON string of `{table_name: [column_names]}`.

---

#### `text_to_sql(schema: str, prompt: str) -> str`

Sends the schema JSON and the user's natural language question to an Ollama-hosted LLM. The model is instructed to return only valid SQL with no preamble, no markdown fences, and no `<think>` tags.

**Parameters:**
| Name   | Type | Description                          |
|--------|------|--------------------------------------|
| schema | str  | JSON schema string (from `extract_schema`) |
| prompt | str  | Natural language question             |

**Returns:** Cleaned SQL query string.

**Processing:**
1. Constructs a `ChatPromptTemplate` with a system prompt and user message.
2. Invokes the LLM via `OllamaLLM` at `temperature=0` for deterministic output.
3. Strips any `<think>...</think>` blocks (common in reasoning models like DeepSeek-R1).

---

#### `get_data_from_database(prompt: str, db_url: str) -> list`

Orchestrates the full pipeline: extract schema → text-to-SQL → execute → return.

**Parameters:**
| Name   | Type | Description                           |
|--------|------|---------------------------------------|
| prompt | str  | Natural language question             |
| db_url | str  | SQLAlchemy database URL (default: `sqlite:///amazon.db`) |

**Returns:** List of tuples — the raw result set from the executed query.

**Database URLs by type:**

| Database    | URL Format                                             |
|-------------|--------------------------------------------------------|
| SQLite      | `sqlite:///path/to/database.db`                       |
| PostgreSQL  | `postgresql://user:password@host:port/database`       |
| MySQL       | `mysql://user:password@host:port/database`            |

---

### `frontend.py` — Streamlit UI

A connection-first Streamlit interface. Users configure their database via the sidebar before asking questions.

**Connection workflow:**

1. **Sidebar** — Select database type (SQLite, PostgreSQL, MySQL) and enter connection details.
2. **Connect** — Tests the connection by inspecting available tables and stores the connection in session state.
3. **Query** — After connection, enter natural language questions and receive results.

**Key components:**
- `st.sidebar` — Connection form with dynamic fields based on database type.
- Table listing — Shows available tables after successful connection.
- `st.dataframe` — Displays query results in a formatted table.
- Session state — Maintains connection across reruns.

**Run:**
```bash
uv run streamlit run frontend.py
```

---

### `create_database.py` — Database Bootstrap

Creates the SQLite database `amazon.db` with four related tables and populates them with sample data.

**Tables created:**

| Table         | Description                         |
|---------------|-------------------------------------|
| `customers`   | Customer records (name, email, city, join_date) |
| `products`    | Product catalog (name, category, price) |
| `orders`      | Order headers linked to customers   |
| `order_items` | Line items linking orders to products with quantity and subtotal |

**Sample data includes:**
- 4 customers (Alice, Bob, Charlie, Diana)
- 5 products (Mouse, Laptop Sleeve, Headphones, Water Bottle, Notebook)
- 4 orders with 6 order items

---

### `db_mcp_server.py` — MCP Database Creation Tool

An MCP (Model Context Protocol) server that exposes a `create_database` tool. The tool accepts a natural language description of a database and uses an LLM to determine the schema, then creates a SQLite database file with the appropriate tables and columns.

**Exposed tool:**

| Tool              | Description                                                    |
|-------------------|----------------------------------------------------------------|
| `create_database` | Creates a SQLite database from a natural language description. |

**`create_database` parameters:**

| Name         | Type   | Required | Description                                          |
|--------------|--------|----------|------------------------------------------------------|
| description  | string | Yes      | Natural language description of the database to create |
| output_dir   | string | No       | Directory to create the database in (default: `.`)   |

**Return value:**

```json
{
  "database": "my_database.db",
  "path": "/absolute/path/to/my_database.db",
  "tables_created": ["users", "tasks"],
  "table_count": 2
}
```

**How it works:**
1. Receives a natural language description via the MCP tool call.
2. Sends the description to the local Ollama LLM with a structured prompt requesting JSON output.
3. Parses the LLM's JSON response into a database specification.
4. Creates the SQLite database file and executes `CREATE TABLE` statements.

**Run:**
```bash
uv run python db_mcp_server.py
```

The server reads JSON-RPC 2.0 messages from stdin and writes responses to stdout, following the MCP protocol.

---

## Database Schema

The sample `amazon.db` follows this schema:

```sql
customers
├── customer_id INTEGER PRIMARY KEY
├── name        TEXT
├── email       TEXT
├── city        TEXT
└── join_date   TEXT

products
├── product_id  INTEGER PRIMARY KEY
├── name        TEXT
├── category    TEXT
└── price       REAL

orders
├── order_id    INTEGER PRIMARY KEY
├── customer_id INTEGER → customers(customer_id)
├── order_date  TEXT
└── total_amount REAL

order_items
├── order_item_id INTEGER PRIMARY KEY
├── order_id      INTEGER → orders(order_id)
├── product_id    INTEGER → products(product_id)
├── quantity      INTEGER
└── subtotal      REAL
```

---

## API Reference

### `get_data_from_database(prompt: str, db_url: str = "sqlite:///amazon.db") -> list[tuple]`

The primary public API. Suitable for integration into other Python scripts, notebooks, or REST backends.

```python
from main import get_data_from_database

# Query the default SQLite database
results = get_data_from_database("How many orders did Alice place?")
# Returns: [(2,)]

# Query a PostgreSQL database
results = get_data_from_database(
    "List all users who signed up this month",
    db_url="postgresql://user:pass@localhost:5432/mydb"
)
```

---

## Usage Examples

### Basic Query (SQLite)

```python
from main import get_data_from_database

results = get_data_from_database("List all products in the Electronics category")
print(results)
# Output: [('Wireless Mouse', 'Electronics', 25.99), ('Bluetooth Headphones', 'Electronics', 45.99)]
```

### Aggregation Query

```python
results = get_data_from_database("What is the total revenue from all orders?")
print(results)
# Output: [(168.95,)]
```

### Join Query

```python
results = get_data_from_database("Show me customer names and their order dates")
print(results)
# Output: [('Alice Johnson', '2024-05-05'), ('Bob Smith', '2024-05-07'), ...]
```

### Custom Database URL

```python
results = get_data_from_database(
    "Most expensive products",
    db_url="sqlite:///my_store.db"
)
```

### Via Streamlit

```bash
uv run streamlit run frontend.py
```

1. Select database type and enter credentials in the sidebar.
2. Click **Connect**.
3. Enter a question like *"Which city has the most customers?"*.
4. Click **Analyze** to see results.

### MCP: Create a Database from Natural Language

Configure the MCP server in your client:

```json
{
  "mcpServers": {
    "db-creator": {
      "command": "uv",
      "args": ["run", "python", "db_mcp_server.py"]
    }
  }
}
```

Then send a request like:
> *"Create a project management database with users, projects, and tasks tables. Users should have name and email, projects have name and deadline, tasks have title, status, and assigned user."*

The server will create a SQLite database with the appropriate schema.

---

## MCP Server

The `db_mcp_server.py` implements an MCP (Model Context Protocol) server that communicates via JSON-RPC 2.0 over stdio.

### Protocol

| Method               | Purpose                            |
|----------------------|------------------------------------|
| `initialize`         | Server handshake                   |
| `tools/list`         | Returns available tool definitions |
| `tools/call`         | Executes a tool with arguments     |

### Configuration

To use with **opencode**, add to your `opencode.json`:

```json
{
  "mcpServers": {
    "db-creator": {
      "command": "uv",
      "args": ["run", "python", "db_mcp_server.py"]
    }
  }
}
```

To use with **Claude Desktop**, add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "db-creator": {
      "command": "uv",
      "args": ["run", "python", "db_mcp_server.py"]
    }
  }
}
```

### Prompt Examples

| Input                                                                    | Result                                        |
|--------------------------------------------------------------------------|-----------------------------------------------|
| *"Create a todo list database with users and tasks"*                     | `todo_list.db` with `users` and `tasks` tables |
| *"Make a CRM database for tracking contacts and deals"*                  | `crm.db` with `contacts` and `deals` tables    |
| *"Create an e-commerce database with products, customers, and orders"*   | `e_commerce.db` with three tables with FKs     |

---

## Model Configuration

Edit the model instantiation in `main.py`:

```python
model = OllamaLLM(model="deepseek-r1:8b", temperature=0)
```

**Recommended models:**

| Model                  | Speed  | Quality | Notes                              |
|------------------------|--------|---------|------------------------------------|
| `qwen2.5-coder:7b`    | Fast   | Good    | Best balance for SQL generation    |
| `deepseek-r1:8b`      | Slow   | High    | Generates reasoning in `<think>` tags (automatically stripped) |
| `codellama:7b`        | Medium | Good    | Solid SQL capabilities             |

**Important:** Always set `temperature=0` for deterministic, reproducible SQL output.

---

## Security Considerations

Executing LLM-generated SQL on your database carries inherent risk. The following mitigations are **recommended**:

### Read-Only Enforcement

Add a guard in `main.py` to reject non-`SELECT` queries:

```python
if not sql_query.strip().lower().startswith("select"):
    raise ValueError("Only SELECT queries are permitted.")
```

### Dangerous Keyword Blocking

```python
blocked = ["drop", "delete", "update", "insert", "alter", "create", "truncate"]
for keyword in blocked:
    if keyword in sql_query.lower():
        raise ValueError(f"Query blocked: contains '{keyword}'")
```

### Database User Permissions

For production use, connect with a database user that has **read-only** privileges.

### Input Sanitization

If user input is interpolated into the prompt (it currently is, via the template), ensure it is logged and sanitized to prevent prompt injection.

---

## Troubleshooting

| Issue                          | Likely Cause                     | Fix                                                      |
|--------------------------------|----------------------------------|----------------------------------------------------------|
| Long response time             | Reasoning model (DeepSeek-R1)    | Switch to `qwen2.5-coder:7b`                             |
| SQL errors ("no such column")  | Model hallucinated column names  | Verify schema is correct; strengthen system prompt       |
| Empty results                  | Valid query, no matching data    | Inspect database contents directly                       |
| Ollama connection error        | Ollama service not running       | Run `ollama serve` or start the Ollama desktop app       |
| `<think>` tags in output       | Reasoning model                  | Already stripped by `re.sub` — verify regex is working   |
| `uv` command not found         | `uv` not installed               | Run the Astral install script (see Setup section)        |
| MCP server not connecting      | Configuration error              | Verify `opencode.json` command and args are correct      |
| Database connection fails      | Wrong credentials or URL         | Verify connection string; check host/port accessibility  |

---

## Roadmap

- [x] Core text-to-SQL pipeline
- [x] Streamlit frontend with connection-first workflow
- [x] Multi-database support (SQLite, PostgreSQL, MySQL)
- [x] MCP server for database creation from natural language
- [ ] SQL validation and sandboxing layer
- [ ] Caching layer for repeated queries
- [ ] Unit tests for `text_to_sql`, `extract_schema`, and MCP server
- [ ] Query result visualization (charts in Streamlit)
- [ ] Conversation memory for multi-turn queries

---

## Development

### Adding Dependencies

```bash
uv add package-name
```

### Upgrading Dependencies

```bash
uv lock --upgrade
uv sync
```

### Compile Check

```bash
uv run python -m py_compile main.py
uv run python -m py_compile frontend.py
uv run python -m py_compile db_mcp_server.py
```

---

## License

MIT — see `pyproject.toml` for details.

---

*Built with LangChain, Ollama, and Python tooling.*
