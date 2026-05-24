from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import ReadExcelTool, ReadCSVTool, ListTablesTool, GetSchemaTool


def create_ingestion_agent() -> Agent:
    config = AGENT_CONFIG["ingestion"]
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=[ReadExcelTool(), ReadCSVTool(), ListTablesTool(), GetSchemaTool()],
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
