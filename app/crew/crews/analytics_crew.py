from crewai import Crew, Process

from app.crew.agents.ingestion_agent import create_ingestion_agent
from app.crew.agents.sql_analyst_agent import create_sql_analyst_agent
from app.crew.agents.visualization_agent import create_visualization_agent
from app.crew.agents.insights_agent import create_insights_agent
from app.crew.agents.qa_agent import create_qa_agent

from app.crew.tasks.ingestion_tasks import create_ingestion_task
from app.crew.tasks.sql_tasks import create_sql_task
from app.crew.tasks.visualization_tasks import create_visualization_task
from app.crew.tasks.insights_tasks import create_insights_task
from app.crew.tasks.qa_tasks import create_qa_task

from app.crew.memory.memory_manager import memory_manager
from app.config.settings import CREWAI_VERBOSE
from app.utils.logging import logger


class AnalyticsCrew:
    def __init__(self):
        self.ingestion_agent = create_ingestion_agent()
        self.sql_agent = create_sql_analyst_agent()
        self.viz_agent = create_visualization_agent()
        self.insights_agent = create_insights_agent()
        self.qa_agent = create_qa_agent()

    def run(self, question: str, table_name: str | None = None, file_path: str | None = None) -> dict:
        tasks = []
        agents_used = []

        if file_path:
            ingest_task = create_ingestion_task(self.ingestion_agent, file_path=file_path)
            tasks.append(ingest_task)
            agents_used.append("ingestion")

        if table_name:
            qa_check = create_qa_task(self.qa_agent, table_name, context=f"Validating data quality before analysis. Question: {question}")
            tasks.append(qa_check)
            agents_used.append("qa")

            sql_task = create_sql_task(self.sql_agent, table_name, question)
            tasks.append(sql_task)
            agents_used.append("sql_analyst")

            viz_task = create_visualization_task(self.viz_agent, table_name, context=f"Question: {question}")
            tasks.append(viz_task)
            agents_used.append("visualization")

            insights_task = create_insights_task(self.insights_agent, table_name, context=f"Question: {question}")
            tasks.append(insights_task)
            agents_used.append("insights")

        if not tasks:
            return {"error": "No tasks to execute", "agents_used": []}

        crew = Crew(
            agents=list(set([self.ingestion_agent, self.sql_agent, self.viz_agent, self.insights_agent, self.qa_agent])),
            tasks=tasks,
            process=Process.sequential,
            verbose=CREWAI_VERBOSE,
        )

        try:
            result = crew.kickoff()
            memory_manager.add_conversation("main", "user", question)
            memory_manager.add_conversation("main", "assistant", str(result))

            return {
                "result": str(result),
                "agents_used": agents_used,
                "tasks_count": len(tasks),
            }
        except Exception as e:
            logger.error(f"Analytics crew failed: {e}")
            return {"error": str(e), "agents_used": agents_used}
