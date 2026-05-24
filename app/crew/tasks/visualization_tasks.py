from crewai import Task


def create_visualization_task(agent, table_name: str, chart_type: str = "auto", context: str = "") -> Task:
    return Task(
        description=f"""Create visualizations from table '{table_name}'.
Chart type: {chart_type}
Context: {context}

1. Examine the table schema and data profile
2. Determine the best columns to visualize
3. Generate appropriate charts
4. If suitable, create a full dashboard
5. Return the chart configurations and insights""",
        expected_output="Description of charts/dashboard created with chart type selections and rationale",
        agent=agent,
    )
