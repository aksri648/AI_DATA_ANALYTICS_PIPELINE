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
    def _build_data_context(self, df, profile, validation) -> str:
        """Build a rich data context string with actual values for the LLM."""
        import numpy as np
        parts = []
        parts.append(f"DATASET: {len(df)} rows × {len(df.columns)} columns")
        parts.append(f"COLUMNS: {', '.join(df.columns.tolist())}")
        parts.append("")

        parts.append("SAMPLE ROWS (first 5):")
        parts.append(df.head(5).to_string(index=False))
        parts.append("")

        numeric = df.select_dtypes(include=[np.number])
        if not numeric.empty:
            parts.append("NUMERIC COLUMNS SUMMARY:")
            desc = numeric.describe().T
            desc["missing"] = numeric.isnull().sum()
            desc["unique"] = numeric.nunique()
            for col in desc.index:
                row = desc.loc[col]
                parts.append(
                    f"  {col}: mean={row['mean']:.2f}, median={row['50%']:.2f}, "
                    f"min={row['min']:.2f}, max={row['max']:.2f}, "
                    f"std={row['std']:.2f}, missing={int(row['missing'])}, unique={int(row['unique'])}"
                )
            parts.append("")

        categorical = df.select_dtypes(include=["object", "category"])
        if not categorical.empty:
            parts.append("CATEGORICAL COLUMNS DISTRIBUTION:")
            for col in categorical.columns[:8]:
                vc = df[col].value_counts()
                top_vals = ", ".join(f"{k}={v}" for k, v in vc.head(8).items())
                parts.append(f"  {col} ({df[col].nunique()} unique): {top_vals}")
            parts.append("")

        if len(numeric.columns) >= 2:
            corr = numeric.corr()
            pairs = []
            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    val = corr.iloc[i, j]
                    if abs(val) > 0.3:
                        pairs.append((corr.columns[i], corr.columns[j], val))
            if pairs:
                pairs.sort(key=lambda x: abs(x[2]), reverse=True)
                parts.append("NOTABLE CORRELATIONS:")
                for c1, c2, v in pairs[:10]:
                    parts.append(f"  {c1} ↔ {c2}: {v:.3f}")
                parts.append("")

        if not categorical.empty and not numeric.empty:
            cat_col = categorical.columns[0]
            parts.append(f"GROUP-BY ANALYSIS (by {cat_col}):")
            for ncol in numeric.columns[:4]:
                grp = df.groupby(cat_col)[ncol].agg(["mean", "sum", "count"]).round(2)
                for idx in grp.index:
                    row = grp.loc[idx]
                    parts.append(f"  {cat_col}={idx}: avg_{ncol}={row['mean']}, total_{ncol}={row['sum']}, count={int(row['count'])}")
            parts.append("")

        if validation and validation.get("outliers"):
            outlier_cols = validation["outliers"]
            if isinstance(outlier_cols, dict):
                parts.append("OUTLIERS DETECTED:")
                for col, info in outlier_cols.items():
                    if isinstance(info, dict) and info.get("count", 0) > 0:
                        parts.append(f"  {col}: {info['count']} outliers ({info.get('percentage', 0):.1f}%)")
                parts.append("")

        return "\n".join(parts)

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

    def clean_chat_markdown(self, text: str) -> str:
        text = re.sub(r"```sql\s*.*?```", "", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"```\s*.*?```", "", text, flags=re.DOTALL)
        return text.strip()

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
            data_context = self._build_data_context(df, profile, validation)
            prompt = f"""You are a senior business intelligence analyst. Analyze the ACTUAL DATA VALUES below and provide genuine business insights — not descriptions of the data structure.

{data_context}

User question: {question}

Rules:
- Do NOT describe the dataset structure, column names, or data types.
- Analyze the actual VALUES and derive business conclusions.
- Reference real numbers, percentages, and comparisons from the data.
- Give the final answer directly as short markdown bullets and a concise conclusion.
- Focus on what the data MEANS, not what columns exist.
- If the user asked a specific question, answer it with data-backed evidence."""
            insights = self.clean_chat_markdown(ollama_service.invoke(prompt))
            return {"intent": intent, "insights": insights, "table_name": table_name, "profile": profile}

        if intent == "report":
            validation = DataValidation.validate_dataset(df)
            kpis = chart_engine.generate_kpi_cards(df)

            prompt = f"""Generate an executive summary for this dataset:

Profile: {profile}
KPIs: {kpis}
User context: {question}

Write a concise 2-3 paragraph executive summary."""
            summary = ollama_service.invoke(prompt)

            recs_prompt = f"""Based on this dataset, provide 5 actionable recommendations:
Profile: {profile}
User context: {question}"""
            recs_text = ollama_service.invoke(recs_prompt)
            recommendations = [l for l in recs_text.split("\n") if l.strip() and not l.startswith("#")][:5]

            report_figures = chart_engine.generate_report_charts(df)
            charts_html = {}
            for name, fig in report_figures.items():
                if fig is not None:
                    charts_html[name] = chart_engine.figure_to_html(fig)

            report = report_generator.generate_html_report(
                "Analytics Report", summary, kpis, [summary], charts_html, recommendations=recommendations
            )
            return {"intent": intent, "report": report, "table_name": table_name}

        data_context = self._build_data_context(df, profile, None)
        prompt = f"""You are a senior business intelligence analyst. Analyze the ACTUAL DATA VALUES below and answer the user's question with genuine insights.

{data_context}

Question: {question}

Rules:
- Do NOT describe the dataset structure, column names, or data types.
- Analyze the actual VALUES and provide a direct answer with evidence.
- Reference real numbers, percentages, and comparisons from the data.
- Give the final answer directly with clear markdown bullets and a concise conclusion.
- If the user asked a specific question, answer it with data-backed evidence.
- Do not include code blocks or SQL."""
        analysis = self.clean_chat_markdown(ollama_service.invoke(prompt))
        fig = chart_engine.auto_chart(df, question)
        return {
            "intent": intent,
            "analysis": analysis,
            "chart": fig.to_html(include_plotlyjs="cdn", full_html=False) if fig else None,
            "table_name": table_name,
        }


analytics_service = AnalyticsService()
