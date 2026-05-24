from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import GenerateChartTool, CreateDashboardTool, QuerySQLTool, GetSchemaTool


def create_visualization_agent() -> Agent:
    config = AGENT_CONFIG["visualization"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[GenerateChartTool(), CreateDashboardTool(), QuerySQLTool(), GetSchemaTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
