from crewai import Crew, Process

from app.crew.agents.ingestion_agent import create_ingestion_agent
from app.crew.agents.etl_agent import create_etl_agent
from app.crew.agents.qa_agent import create_qa_agent

from app.crew.tasks.ingestion_tasks import create_ingestion_task
from app.crew.tasks.etl_tasks import create_etl_task
from app.crew.tasks.qa_tasks import create_qa_task

from app.crew.memory.memory_manager import memory_manager
from app.config.settings import CREWAI_VERBOSE
from app.utils.logging import logger


class ETLCrew:
    def __init__(self):
        self.ingestion_agent = create_ingestion_agent()
        self.etl_agent = create_etl_agent()
        self.qa_agent = create_qa_agent()

    def run(self, file_path: str | None = None, table_name: str | None = None) -> dict:
        tasks = []
        agents_used = []

        if file_path:
            ingest_task = create_ingestion_task(self.ingestion_agent, file_path=file_path)
            tasks.append(ingest_task)
            agents_used.append("ingestion")

        target_table = table_name

        if not target_table and file_path:
            import os
            target_table = os.path.splitext(os.path.basename(file_path))[0].lower().replace(" ", "_")

        if target_table:
            etl_task = create_etl_task(self.etl_agent, target_table)
            tasks.append(etl_task)
            agents_used.append("etl")

            qa_task = create_qa_task(self.qa_agent, target_table, context="Validate ETL output quality")
            tasks.append(qa_task)
            agents_used.append("qa")

        if not tasks:
            return {"error": "No tasks to execute", "agents_used": []}

        crew = Crew(
            agents=list(set([self.ingestion_agent, self.etl_agent, self.qa_agent])),
            tasks=tasks,
            process=Process.sequential,
            verbose=CREWAI_VERBOSE,
        )

        try:
            result = crew.kickoff()
            return {
                "result": str(result),
                "agents_used": agents_used,
                "tasks_count": len(tasks),
            }
        except Exception as e:
            logger.error(f"ETL crew failed: {e}")
            return {"error": str(e), "agents_used": agents_used}
