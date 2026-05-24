from crewai import Task


def create_insights_task(agent, table_name: str, context: str = "") -> Task:
    return Task(
        description=f"""Generate business insights from table '{table_name}'.
Context: {context}

1. Profile the data to understand key metrics
2. Identify trends, patterns, and anomalies
3. Generate actionable business insights
4. Provide specific recommendations
5. Return a structured insights report""",
        expected_output="Structured insights report with findings, patterns, and recommendations",
        agent=agent,
    )
