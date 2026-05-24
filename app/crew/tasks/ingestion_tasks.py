from crewai import Task


def create_ingestion_task(agent, file_path: str = "", table_name: str = "", context: str = "") -> Task:
    return Task(
        description=f"""Ingest data into the warehouse.
File: {file_path}
Table name: {table_name}
Context: {context}

1. Determine the file type and read the data
2. Load the data into the warehouse
3. List available tables to confirm ingestion
4. Get the schema of the ingested table
5. Return the table name, row count, and column names""",
        expected_output="Summary of the ingested data including table name, row count, and column schema",
        agent=agent,
    )
