from crewai import Task


def create_sql_task(agent, table_name: str, question: str) -> Task:
    return Task(
        description=f"""Answer the user's question by querying table '{table_name}'.
Question: {question}

1. First get the schema of the table to understand its columns
2. Formulate a SQL query that answers the question
3. Execute the query
4. Return the results with a brief explanation""",
        expected_output="SQL query results with explanation answering the user's question",
        agent=agent,
    )
