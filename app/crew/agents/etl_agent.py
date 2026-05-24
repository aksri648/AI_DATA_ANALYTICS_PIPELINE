from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import CleanDataTool, ProfileDataTool, QuerySQLTool, GetSchemaTool


def create_etl_agent() -> Agent:
    config = AGENT_CONFIG["etl"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[CleanDataTool(), ProfileDataTool(), QuerySQLTool(), GetSchemaTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
