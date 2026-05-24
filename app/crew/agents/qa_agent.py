from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import ProfileDataTool, QuerySQLTool, GetSchemaTool


def create_qa_agent() -> Agent:
    config = AGENT_CONFIG["qa"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[ProfileDataTool(), QuerySQLTool(), GetSchemaTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
