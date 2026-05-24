from crewai.tools import BaseTool
from typing import Type, Any
from pydantic import BaseModel, Field

from app.mcp.tools import MCPTools
from app.db.warehouse import warehouse
from app.charts.chart_engine import chart_engine
from app.charts.dashboard_builder import dashboard_builder
from app.etl.profiling import DataProfiling
from app.etl.validation import DataValidation
from app.utils.logging import logger


class ReadExcelToolInput(BaseModel):
    file_path: str = Field(description="Path to the Excel file")
    sheet_name: str | int = Field(default=0, description="Sheet name or index")
    table_name: str | None = Field(default=None, description="Target table name")

class ReadExcelTool(BaseTool):
    name: str = "read_excel"
    description: str = "Read an Excel file and load it into the data warehouse"
    args_schema: Type[BaseModel] = ReadExcelToolInput

    def _run(self, file_path: str, sheet_name: str | int = 0, table_name: str | None = None) -> str:
        result = MCPTools.execute_tool("read_excel", {"file_path": file_path, "sheet_name": sheet_name, "table_name": table_name})
        return str(result)


class ReadCSVToolInput(BaseModel):
    file_path: str = Field(description="Path to the CSV file")
    table_name: str | None = Field(default=None, description="Target table name")

class ReadCSVTool(BaseTool):
    name: str = "read_csv"
    description: str = "Read a CSV file and load it into the data warehouse"
    args_schema: Type[BaseModel] = ReadCSVToolInput

    def _run(self, file_path: str, table_name: str | None = None) -> str:
        result = MCPTools.execute_tool("read_csv", {"file_path": file_path, "table_name": table_name})
        return str(result)


class QuerySQLToolInput(BaseModel):
    sql: str = Field(description="SELECT SQL query to execute")

class QuerySQLTool(BaseTool):
    name: str = "query_sql"
    description: str = "Execute a read-only SELECT SQL query on the data warehouse"
    args_schema: Type[BaseModel] = QuerySQLToolInput

    def _run(self, sql: str) -> str:
        result = MCPTools.execute_tool("query_sql", {"sql": sql})
        return str(result)


class ProfileDataToolInput(BaseModel):
    table_name: str = Field(description="Name of the table to profile")

class ProfileDataTool(BaseTool):
    name: str = "profile_data"
    description: str = "Generate a full statistical profile of a dataset"
    args_schema: Type[BaseModel] = ProfileDataToolInput

    def _run(self, table_name: str) -> str:
        result = MCPTools.execute_tool("profile_data", {"table_name": table_name})
        return str(result)


class CleanDataToolInput(BaseModel):
    table_name: str = Field(description="Name of the table to clean")

class CleanDataTool(BaseTool):
    name: str = "clean_data"
    description: str = "Automatically clean a dataset (remove duplicates, handle nulls, standardize)"
    args_schema: Type[BaseModel] = CleanDataToolInput

    def _run(self, table_name: str) -> str:
        result = MCPTools.execute_tool("clean_data", {"table_name": table_name})
        return str(result)


class GenerateChartToolInput(BaseModel):
    table_name: str = Field(description="Table name to chart from")
    chart_type: str = Field(default="auto", description="Chart type: auto, line, bar, pie, scatter")
    x_column: str | None = Field(default=None, description="X-axis column")
    y_column: str | None = Field(default=None, description="Y-axis column")

class GenerateChartTool(BaseTool):
    name: str = "generate_chart"
    description: str = "Generate a Plotly chart from data in the warehouse"
    args_schema: Type[BaseModel] = GenerateChartToolInput

    def _run(self, table_name: str, chart_type: str = "auto", x_column: str | None = None, y_column: str | None = None) -> str:
        result = MCPTools.execute_tool("generate_chart", {
            "table_name": table_name, "chart_type": chart_type,
            "x_column": x_column, "y_column": y_column,
        })
        return str(result)


class CreateDashboardToolInput(BaseModel):
    table_name: str = Field(description="Table name to build dashboard from")
    dashboard_type: str = Field(default="auto", description="Type: auto, sales, finance, hr, marketing")

class CreateDashboardTool(BaseTool):
    name: str = "create_dashboard"
    description: str = "Generate an automatic dashboard from a dataset with KPIs and charts"
    args_schema: Type[BaseModel] = CreateDashboardToolInput

    def _run(self, table_name: str, dashboard_type: str = "auto") -> str:
        result = MCPTools.execute_tool("create_dashboard", {"table_name": table_name, "dashboard_type": dashboard_type})
        return str(result)


class ListTablesToolInput(BaseModel):
    pass

class ListTablesTool(BaseTool):
    name: str = "list_tables"
    description: str = "List all available tables in the data warehouse"
    args_schema: Type[BaseModel] = ListTablesToolInput

    def _run(self) -> str:
        tables = warehouse.list_datasets()
        return str(tables)


class GetSchemaToolInput(BaseModel):
    table_name: str = Field(description="Name of the table to describe")

class GetSchemaTool(BaseTool):
    name: str = "get_schema"
    description: str = "Get the schema of a table (column names and types)"
    args_schema: Type[BaseModel] = GetSchemaToolInput

    def _run(self, table_name: str) -> str:
        try:
            schema = warehouse.get_profile(table_name)
            return str(schema.to_dict(orient="records"))
        except Exception as e:
            return f"Error: {e}"


class GenerateInsightsToolInput(BaseModel):
    table_name: str = Field(description="Table name to analyze")
    context: str = Field(default="", description="Additional context about what to look for")

class GenerateInsightsTool(BaseTool):
    name: str = "generate_insights"
    description: str = "Generate AI business insights from a dataset"
    args_schema: Type[BaseModel] = GenerateInsightsToolInput

    def _run(self, table_name: str, context: str = "") -> str:
        try:
            df = warehouse.get_dataset(table_name)
            profile = DataProfiling.full_profile(df)
            validation = DataValidation.validate_dataset(df)
            from app.llm.ollama_service import ollama_service
            prompt = f"""Analyze this dataset profile and generate 5 key business insights:

Profile: {profile}
Validation: {validation}
User context: {context}

Generate specific, actionable insights about trends, patterns, anomalies, and opportunities."""
            insights = ollama_service.invoke(prompt)
            return insights
        except Exception as e:
            return f"Error generating insights: {e}"


tool_registry = {
    "read_excel": ReadExcelTool(),
    "read_csv": ReadCSVTool(),
    "query_sql": QuerySQLTool(),
    "profile_data": ProfileDataTool(),
    "clean_data": CleanDataTool(),
    "generate_chart": GenerateChartTool(),
    "create_dashboard": CreateDashboardTool(),
    "list_tables": ListTablesTool(),
    "get_schema": GetSchemaTool(),
    "generate_insights": GenerateInsightsTool(),
}
