from crewai import Crew, Process

from app.crew.agents.insights_agent import create_insights_agent
from app.crew.agents.visualization_agent import create_visualization_agent
from app.crew.agents.report_agent import create_report_agent
from app.crew.agents.qa_agent import create_qa_agent

from app.crew.tasks.insights_tasks import create_insights_task
from app.crew.tasks.visualization_tasks import create_visualization_task
from app.crew.tasks.report_tasks import create_report_task
from app.crew.tasks.qa_tasks import create_qa_task

from app.config.settings import CREWAI_VERBOSE
from app.utils.logging import logger


class ReportCrew:
    def __init__(self):
        self.insights_agent = create_insights_agent()
        self.viz_agent = create_visualization_agent()
        self.report_agent = create_report_agent()
        self.qa_agent = create_qa_agent()

    def run(self, table_name: str, title: str = "Analytics Report", context: str = "") -> dict:
        tasks = [
            create_insights_task(self.insights_agent, table_name, context),
            create_visualization_task(self.viz_agent, table_name, context=context),
            create_report_task(self.report_agent, table_name, title, context),
            create_qa_task(self.qa_agent, table_name, context=f"Validate report for {title}"),
        ]

        crew = Crew(
            agents=[self.insights_agent, self.viz_agent, self.report_agent, self.qa_agent],
            tasks=tasks,
            process=Process.sequential,
            verbose=CREWAI_VERBOSE,
        )

        try:
            result = crew.kickoff()
            return {
                "result": str(result),
                "agents_used": ["insights", "visualization", "report", "qa"],
                "tasks_count": len(tasks),
            }
        except Exception as e:
            logger.error(f"Report crew failed: {e}")
            return {"error": str(e), "agents_used": []}
