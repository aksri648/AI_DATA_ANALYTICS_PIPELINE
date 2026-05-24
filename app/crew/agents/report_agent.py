from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import ProfileDataTool, QuerySQLTool, GetSchemaTool, GenerateInsightsTool


def create_report_agent() -> Agent:
    config = AGENT_CONFIG["report"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[ProfileDataTool(), QuerySQLTool(), GetSchemaTool(), GenerateInsightsTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
