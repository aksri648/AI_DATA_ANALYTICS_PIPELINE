from typing import Any
import re

import pandas as pd

from app.llm.ollama_service import ollama_service
from app.db.warehouse import warehouse
from app.charts.chart_engine import chart_engine
from app.charts.dashboard_builder import dashboard_builder
from app.etl.profiling import DataProfiling
from app.etl.validation import DataValidation
from app.reports.report_generator import report_generator
from app.utils.logging import logger


class AnalyticsService:
    def detect_intent(self, question: str) -> str:
        q = question.lower()
        words = set(re.findall(r"\b[a-z_]+\b", q))
        if any(p in q for p in ["summarize", "summarise", "conclusion", "key takeaway", "takeaways"]):
            return "insights"
        if any(w in q for w in ["read file", "open file"]) or words & {"upload", "import", "load", "ingest"}:
            return "ingestion"
        if any(w in q for w in ["remove duplicate", "fix data"]) or words & {"clean", "etl", "transform"}:
            return "etl"
        if any(w in q for w in ["show me"]) or words & {"chart", "plot", "graph", "visualize", "dashboard"}:
            return "visualization"
        if any(w in q for w in ["why did", "what caused"]) or words & {"insight", "trend", "pattern", "analyze", "analyse"}:
            return "insights"
        if words & {"report", "summary", "executive"}:
            return "report"
        if any(w in q for w in ["group by"]) or words & {"sql", "query", "select", "count", "sum", "average"}:
            return "sql"
        return "analytics"

    def extract_select_sql(self, text: str) -> str | None:
        fenced = re.search(r"```sql\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        candidate = fenced.group(1).strip() if fenced else text.strip()
        match = re.search(r"\bselect\b[\s\S]*?(?:;|$)", candidate, flags=re.IGNORECASE)
        if not match:
            return None
        sql = match.group(0).strip()
        return sql if sql.lower().startswith("select") else None

    def process_question(self, question: str, table_name: str | None = None) -> dict[str, Any]:
        intent = self.detect_intent(question)
        logger.info(f"Detected intent: {intent} for question: {question[:100]}")

        if intent == "ingestion":
            return {"intent": intent, "message": "Please upload a file to ingest.", "requires_file": True}

        if not table_name:
            datasets = warehouse.list_datasets()
            if not datasets:
                return {"intent": intent, "message": "No data available. Please upload a file first.", "requires_file": True}
            table_name = datasets[-1]

        df = warehouse.get_dataset(table_name)
        profile = DataProfiling.full_profile(df)

        if intent == "sql":
            schema = warehouse.get_profile(table_name)
            prompt = f"""Given this database schema:
{schema}

User question: {question}

Generate a SQL query and explain the results."""
            sql_result = ollama_service.invoke(prompt)
            sql = self.extract_select_sql(sql_result)
            if not sql:
                return {"intent": "analytics", "analysis": sql_result, "table_name": table_name}
            try:
                result = warehouse.query(sql)
                return {"intent": intent, "sql": sql, "result": result.to_dict(orient="records"), "table_name": table_name}
            except Exception as e:
                return {"intent": intent, "sql": sql, "error": str(e), "table_name": table_name}

        if intent == "visualization":
            fig = chart_engine.auto_chart(df, question)
            dashboard = dashboard_builder.auto_dashboard(df)
            return {
                "intent": intent,
                "chart": fig.to_html(include_plotlyjs="cdn", full_html=False) if fig else None,
                "dashboard": {k: v.to_html(include_plotlyjs="cdn", full_html=False) if v else None for k, v in dashboard.get("charts", {}).items()},
                "kpis": dashboard.get("kpis", []),
                "table_name": table_name,
            }

        if intent == "insights":
            validation = DataValidation.validate_dataset(df)
            prompt = f"""Analyze this dataset and provide 5 key business insights:

Dataset profile: {profile}
Data validation: {validation}
User question: {question}

Provide actionable, specific insights about trends, anomalies, patterns, and opportunities for improvement."""
            insights = ollama_service.invoke(prompt)
            return {"intent": intent, "insights": insights, "table_name": table_name, "profile": profile}

        if intent == "report":
            validation = DataValidation.validate_dataset(df)
            kpis = chart_engine.generate_kpi_cards(df)
            dashboard = dashboard_builder.auto_dashboard(df)

            prompt = f"""Generate an executive summary for this dataset:

Profile: {profile}
KPIs: {kpis}
User context: {question}

Write a concise 2-3 paragraph executive summary."""
            summary = ollama_service.invoke(prompt)

            charts_html = []
            for fig in dashboard.get("charts", {}).values():
                if fig:
                    charts_html.append(fig.to_html(include_plotlyjs="cdn", full_html=False))

            report = report_generator.generate_html_report(
                "Analytics Report", summary, kpis, [summary], charts_html
            )
            return {"intent": intent, "report": report, "table_name": table_name}

        prompt = f"""Analyze this dataset and answer the user's question.

Dataset profile: {profile}
Question: {question}

Provide a comprehensive analysis with specific numbers and findings."""
        analysis = ollama_service.invoke(prompt)
        fig = chart_engine.auto_chart(df, question)
        return {
            "intent": intent,
            "analysis": analysis,
            "chart": fig.to_html(include_plotlyjs="cdn", full_html=False) if fig else None,
            "table_name": table_name,
        }


analytics_service = AnalyticsService()
