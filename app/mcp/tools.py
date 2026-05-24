import json
from typing import Any
import pandas as pd

from app.etl.ingestion import DataIngestion
from app.etl.cleaning import DataCleaning
from app.etl.transformation import DataTransformation
from app.etl.validation import DataValidation
from app.etl.profiling import DataProfiling
from app.charts.chart_engine import chart_engine
from app.charts.dashboard_builder import dashboard_builder
from app.db.warehouse import warehouse
from app.utils.logging import logger


class MCPTools:
    tools_registry: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, description: str, input_schema: dict[str, Any]):
        def decorator(func):
            cls.tools_registry[name] = {
                "name": name,
                "description": description,
                "input_schema": input_schema,
                "handler": func,
            }
            return func
        return decorator

    @classmethod
    def get_tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"],
            }
            for tool in cls.tools_registry.values()
        ]

    @classmethod
    def execute_tool(cls, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in cls.tools_registry:
            return {"error": f"Tool '{name}' not found"}
        try:
            result = cls.tools_registry[name]["handler"](**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"MCP tool '{name}' failed: {e}")
            return {"success": False, "error": str(e)}


@MCPTools.register("read_excel", "Read an Excel file and load it into the warehouse", {
    "type": "object",
    "properties": {
        "file_path": {"type": "string", "description": "Path to the Excel file"},
        "sheet_name": {"type": "string", "description": "Sheet name or index (default: 0)"},
        "table_name": {"type": "string", "description": "Target table name"},
    },
    "required": ["file_path"],
})
def mcp_read_excel(file_path: str, sheet_name: str | int = 0, table_name: str | None = None) -> dict[str, Any]:
    return DataIngestion.ingest_file(file_path, table_name, sheet_name)


@MCPTools.register("read_csv", "Read a CSV file and load it into the warehouse", {
    "type": "object",
    "properties": {
        "file_path": {"type": "string", "description": "Path to the CSV file"},
        "table_name": {"type": "string", "description": "Target table name"},
    },
    "required": ["file_path"],
})
def mcp_read_csv(file_path: str, table_name: str | None = None) -> dict[str, Any]:
    return DataIngestion.ingest_file(file_path, table_name)


@MCPTools.register("query_sql", "Execute a read-only SQL query on the warehouse", {
    "type": "object",
    "properties": {
        "sql": {"type": "string", "description": "SELECT SQL query to execute"},
    },
    "required": ["sql"],
})
def mcp_query_sql(sql: str) -> Any:
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Only SELECT queries are permitted")
    result = warehouse.query(sql)
    return result.to_dict(orient="records") if isinstance(result, pd.DataFrame) else result


@MCPTools.register("clean_data", "Automatically clean a dataset in the warehouse", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Name of the table to clean"},
    },
    "required": ["table_name"],
})
def mcp_clean_data(table_name: str) -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    cleaned_df, steps = DataCleaning.auto_clean(df)
    warehouse.store_dataset(cleaned_df, f"{table_name}_cleaned")
    return {"steps": steps, "rows_before": len(df), "rows_after": len(cleaned_df)}


@MCPTools.register("transform_data", "Apply transformations to a dataset", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Name of the table to transform"},
        "operations": {
            "type": "array",
            "description": "List of transformation operations",
            "items": {"type": "object"},
        },
    },
    "required": ["table_name"],
})
def mcp_transform_data(table_name: str, operations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    if operations:
        for op in operations:
            op_name = op.pop("operation")
            if hasattr(DataTransformation, op_name):
                df = getattr(DataTransformation, op_name)(df, **op)
    warehouse.store_dataset(df, f"{table_name}_transformed")
    return {"rows": len(df), "columns": len(df.columns)}


@MCPTools.register("validate_schema", "Validate the schema and data quality of a dataset", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Name of the table to validate"},
    },
    "required": ["table_name"],
})
def mcp_validate_schema(table_name: str) -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    return DataValidation.validate_dataset(df)


@MCPTools.register("profile_data", "Generate a full data profile of a dataset", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Name of the table to profile"},
    },
    "required": ["table_name"],
})
def mcp_profile_data(table_name: str) -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    return DataProfiling.full_profile(df)


@MCPTools.register("generate_chart", "Generate a chart from data in the warehouse", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Table name to chart from"},
        "chart_type": {"type": "string", "description": "Chart type (auto, line, bar, pie, scatter)"},
        "x_column": {"type": "string", "description": "X-axis column"},
        "y_column": {"type": "string", "description": "Y-axis column"},
    },
    "required": ["table_name"],
})
def mcp_generate_chart(table_name: str, chart_type: str = "auto", x_column: str | None = None, y_column: str | None = None) -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    if chart_type == "auto":
        fig = chart_engine.auto_chart(df)
    elif chart_type == "line" and x_column and y_column:
        fig = chart_engine.create_line_chart(df, x=x_column, y=y_column)
    elif chart_type == "bar" and x_column and y_column:
        fig = chart_engine.create_bar_chart(df, x=x_column, y=y_column)
    elif chart_type == "pie" and x_column and y_column:
        fig = chart_engine.create_pie_chart(df, names=x_column, values=y_column)
    elif chart_type == "scatter" and x_column and y_column:
        fig = chart_engine.create_scatter_plot(df, x=x_column, y=y_column)
    else:
        fig = chart_engine.auto_chart(df)
    return {"chart_html": fig.to_html(include_plotlyjs="cdn", full_html=False)}


@MCPTools.register("summarize_data", "Generate a statistical summary of a dataset", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Name of the table to summarize"},
    },
    "required": ["table_name"],
})
def mcp_summarize_data(table_name: str) -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    desc = df.describe(include="all").to_dict()
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "dtypes": {str(c): str(d) for c, d in df.dtypes.items()},
        "statistics": {str(k): {str(k2): v2 for k2, v2 in v.items()} for k, v in desc.items()},
    }


@MCPTools.register("create_dashboard", "Generate an automatic dashboard from a dataset", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Table name to build dashboard from"},
        "dashboard_type": {"type": "string", "description": "Type: auto, sales, finance, hr, marketing"},
    },
    "required": ["table_name"],
})
def mcp_create_dashboard(table_name: str, dashboard_type: str = "auto") -> dict[str, Any]:
    df = warehouse.get_dataset(table_name)
    dashboard = dashboard_builder.auto_dashboard(df, dashboard_type)
    result = {
        "type": dashboard.get("type", "auto"),
        "kpis": dashboard.get("kpis", []),
        "charts": {},
    }
    for name, fig in dashboard.get("charts", {}).items():
        if fig:
            result["charts"][name] = fig.to_html(include_plotlyjs="cdn", full_html=False)
    return result


@MCPTools.register("generate_report", "Generate a comprehensive analytics report", {
    "type": "object",
    "properties": {
        "table_name": {"type": "string", "description": "Table name to report on"},
        "title": {"type": "string", "description": "Report title"},
        "format": {"type": "string", "description": "Report format: markdown or html"},
    },
    "required": ["table_name", "title"],
})
def mcp_generate_report(table_name: str, title: str, format: str = "markdown") -> dict[str, Any]:
    from app.reports.report_generator import report_generator
    df = warehouse.get_dataset(table_name)
    profile = DataProfiling.full_profile(df)
    validation = DataValidation.validate_dataset(df)
    kpis = chart_engine.generate_kpi_cards(df)
    dashboard = dashboard_builder.auto_dashboard(df)

    summary = f"Analysis of {table_name}: {len(df)} rows with {len(df.columns)} columns."
    insights = [
        f"Dataset contains {len(df):,} records across {len(df.columns)} dimensions",
        f"Data quality: {validation.get('duplicates', {}).get('duplicate_count', 0)} duplicates, {validation.get('missing_values', {}).get('total_missing', 0)} missing values",
    ]

    charts_html = []
    for fig in dashboard.get("charts", {}).values():
        if fig:
            charts_html.append(fig.to_html(include_plotlyjs="cdn", full_html=False))

    if format == "html":
        report = report_generator.generate_html_report(title, summary, kpis, insights, charts_html)
        return {"format": "html", "report": report}
    else:
        report = report_generator.generate_markdown_report(title, summary, kpis, insights, charts_html)
        return {"format": "markdown", "report": report}
