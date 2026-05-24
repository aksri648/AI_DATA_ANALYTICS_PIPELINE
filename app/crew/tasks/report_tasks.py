from crewai import Task


def create_report_task(agent, table_name: str, title: str = "Analytics Report", context: str = "") -> Task:
    return Task(
        description=f"""Generate a comprehensive analytics report for table '{table_name}'.
Title: {title}
Context: {context}

1. Profile the data
2. Generate insights
3. Create a structured report with findings, KPIs, and recommendations
4. Format as a professional markdown report
5. Return the complete report content""",
        expected_output="Complete markdown analytics report with data summary, insights, and recommendations",
        agent=agent,
    )
