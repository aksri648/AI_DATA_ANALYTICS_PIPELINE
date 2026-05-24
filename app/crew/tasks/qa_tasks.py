from crewai import Task


def create_qa_task(agent, table_name: str, previous_output: str = "", context: str = "") -> Task:
    return Task(
        description=f"""Validate the quality of outputs for table '{table_name}'.
Previous output to validate: {previous_output[:500]}
Context: {context}

1. Profile the data to verify its quality
2. Check for data quality issues (duplicates, missing values, outliers)
3. Validate that the previous analysis is consistent with the data
4. Flag any issues or concerns
5. Return a validation report""",
        expected_output="Validation report confirming data quality and analysis accuracy, or listing issues found",
        agent=agent,
    )
