from crewai import Agent
from app.config.settings import AGENT_CONFIG
from app.crew.tools.mcp_tools import tool_registry


def create_mcp_tool_agent() -> Agent:
    config = AGENT_CONFIG["mcp_tool"]
    tools = list(tool_registry.values())
    return Agent(
        name=config["name"],
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        tools=tools,
        allow_delegation=config["allow_delegation"],
        verbose=config["verbose"],
    )
