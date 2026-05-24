from crewai import Task


def create_etl_task(agent, table_name: str, context: str = "") -> Task:
    return Task(
        description=f"""Perform ETL operations on table '{table_name}'.
Context: {context}

1. Profile the data to understand its structure and quality
2. Clean the data (remove duplicates, handle missing values)
3. Verify the cleaned data quality
4. Return the cleaning steps performed and validation results""",
        expected_output="ETL report showing cleaning steps, rows affected, and validation results",
        agent=agent,
    )
