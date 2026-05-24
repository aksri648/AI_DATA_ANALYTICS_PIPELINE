from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import QuerySQLTool, GetSchemaTool, ListTablesTool, ProfileDataTool


def create_sql_analyst_agent() -> Agent:
    config = AGENT_CONFIG["sql_analyst"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[QuerySQLTool(), GetSchemaTool(), ListTablesTool(), ProfileDataTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
