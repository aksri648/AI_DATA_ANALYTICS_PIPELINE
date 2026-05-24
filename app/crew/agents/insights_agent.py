from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import GenerateInsightsTool, ProfileDataTool, QuerySQLTool, GetSchemaTool


def create_insights_agent() -> Agent:
    config = AGENT_CONFIG["insights"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[GenerateInsightsTool(), ProfileDataTool(), QuerySQLTool(), GetSchemaTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
