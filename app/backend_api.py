import os
import sys
import math
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class SafeJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            default=str,
            allow_nan=False,
        ).encode("utf-8")


def sanitize_for_json(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    return obj


def get_etl_service():
    from app.services.etl_service import etl_service
    return etl_service


def get_analytics_service():
    from app.services.analytics_service import analytics_service
    return analytics_service


def get_warehouse():
    from app.db.warehouse import warehouse
    return warehouse


def get_dashboard_store():
    from app.db.dashboard_store import dashboard_store
    return dashboard_store


def get_ollama_service():
    from app.llm.ollama_service import ollama_service
    return ollama_service


def get_chart_engine():
    from app.charts.chart_engine import chart_engine
    return chart_engine


def get_dashboard_builder():
    from app.charts.dashboard_builder import dashboard_builder
    return dashboard_builder


def get_etl_pipeline():
    from app.etl.pipeline_manager import etl_pipeline
    return etl_pipeline


def get_report_generator():
    from app.reports.report_generator import report_generator
    return report_generator


def get_memory_manager():
    from app.crew.memory.memory_manager import memory_manager
    return memory_manager


app = FastAPI(title="AI Analytics API", version="1.0.0", default_response_class=SafeJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Clear DuckDB database on startup."""
    from app.config.settings import DUCKDB_PATH
    import duckdb

    db_path = Path(DUCKDB_PATH)
    if db_path.exists():
        try:
            conn = duckdb.connect(str(db_path))
            tables = conn.execute("SHOW TABLES").fetchall()
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table[0]}")
            conn.close()
            print(f"Cleared {len(tables)} tables from DuckDB on startup")
        except Exception as e:
            print(f"Warning: Could not clear DuckDB: {e}")


@app.get("/api/health")
async def health_check():
    ollama = get_ollama_service()
    warehouse = get_warehouse()
    ollama_ok = ollama.check_health()
    datasets = warehouse.list_datasets()
    return {
        "status": "ok",
        "ollama": {
            "healthy": ollama_ok,
            "base_url": ollama.base_url,
            "model": ollama.model,
        },
        "datasets_count": len(datasets),
    }


@app.get("/api/settings")
async def get_settings():
    from app.config.settings import OLLAMA_MODEL, DUCKDB_PATH
    ollama = get_ollama_service()
    models = []
    if ollama.check_health():
        models = ollama.list_models()
    return {
        "ollama": {
            "base_url": ollama.base_url,
            "model": OLLAMA_MODEL,
            "available_models": models,
        },
        "duckdb_path": DUCKDB_PATH,
    }


@app.post("/api/settings/ollama-url")
async def update_ollama_url(data: dict[str, str]):
    """Update the Ollama server URL."""
    import app.config.settings as settings_module

    url = data.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Update the settings module
    settings_module.OLLAMA_BASE_URL = url

    # Update ollama service URL in-place so all references stay valid
    ollama = get_ollama_service()
    ollama.update_url(url)

    return {"status": "success", "url": url}


@app.get("/api/models")
async def list_models():
    ollama = get_ollama_service()
    if not ollama.check_health():
        raise HTTPException(status_code=503, detail="Ollama is not available")
    return {"models": ollama.list_models()}


@app.get("/api/datasets")
async def list_datasets():
    warehouse = get_warehouse()
    tables = warehouse.list_datasets()
    return {"datasets": tables}


@app.get("/api/datasets/{name}")
async def get_dataset(name: str, rows: int = 100):
    try:
        warehouse = get_warehouse()
        df = warehouse.get_dataset(name)
        preview = df.head(rows)
        return {
            "name": name,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "preview": preview.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/datasets/{name}/profile")
async def get_dataset_profile(name: str):
    try:
        from app.etl.profiling import DataProfiling
        warehouse = get_warehouse()
        df = warehouse.get_dataset(name)
        profile = DataProfiling.full_profile(df)
        return {"name": name, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/datasets/{name}/validate")
async def validate_dataset_endpoint(name: str):
    try:
        from app.etl.validation import DataValidation
        warehouse = get_warehouse()
        df = warehouse.get_dataset(name)
        validation = DataValidation.validate_dataset(df)
        return {"name": name, "validation": validation}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/datasets/{name}/statistics")
async def get_dataset_statistics(name: str):
    try:
        from app.etl.profiling import DataProfiling
        warehouse = get_warehouse()
        df = warehouse.get_dataset(name)
        stats = DataProfiling.descriptive_stats(df)
        missing = DataProfiling.missing_patterns(df)
        return {
            "name": name,
            "statistics": stats.to_dict() if not stats.empty else {},
            "missing": missing.to_dict() if not missing.empty else {},
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/etl/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    table_name: Optional[str] = Form(None),
    run_etl: bool = Form(True),
):
    try:
        from app.config.settings import UPLOAD_DIR
        from app.utils.helpers import sanitize_table_name

        etl = get_etl_service()
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not table_name:
            table_name = sanitize_table_name(Path(file.filename).stem)

        is_pdf = file.filename.lower().endswith(".pdf")

        if is_pdf:
            result = etl.ingest_file(str(file_path), table_name)
            metadata = result.get("metadata", result)
            return {
                "status": "success",
                "table_name": table_name,
                "is_pdf": True,
                "metadata": metadata,
            }
        elif run_etl:
            result = etl.run_full_etl(file_path=str(file_path), name=table_name)
        else:
            result = etl.ingest_file(str(file_path), table_name)

        if isinstance(result, dict) and result.get("status") == "failed":
            raise HTTPException(status_code=400, detail=result.get("error", "ETL failed"))

        final_table = result.get("final_table", table_name) if isinstance(result, dict) else table_name
        return sanitize_for_json({
            "status": "success",
            "table_name": final_table,
            "is_pdf": False,
            "result": result,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etl/clean/{name}")
async def clean_dataset(name: str):
    try:
        etl = get_etl_service()
        result = etl.clean_dataset(name)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etl/profile/{name}")
async def profile_dataset(name: str):
    try:
        etl = get_etl_service()
        profile = etl.profile_dataset(name)
        return {"status": "success", "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/etl/history")
async def get_pipeline_history():
    pipeline = get_etl_pipeline()
    history = pipeline.get_pipeline_history()
    return {"history": history}


@app.post("/api/analytics/chat")
async def analytics_chat(data: dict[str, Any]):
    try:
        analytics = get_analytics_service()
        question = data.get("question", "")
        table_name = data.get("table_name")

        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        result = analytics.process_question(question, table_name)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analytics/insights/{name}")
async def generate_insights(name: str):
    try:
        import numpy as np
        from app.etl.profiling import DataProfiling
        from app.etl.validation import DataValidation

        warehouse = get_warehouse()
        ollama = get_ollama_service()
        chart_eng = get_chart_engine()

        df = warehouse.get_dataset(name)
        profile = DataProfiling.full_profile(df)
        validation = DataValidation.validate_dataset(df)
        kpis = chart_eng.generate_kpi_cards(df)

        parts = []
        parts.append(f"DATASET: {len(df)} rows x {len(df.columns)} columns")
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

        data_context = "\n".join(parts)

        prompt = f"""You are a senior business intelligence analyst. Below is a real dataset. Analyze the ACTUAL DATA VALUES and provide genuine business insights.

{data_context}

Provide your analysis in this format:

## Executive Summary
2-3 sentences describing the most important findings.

## Key Findings
- List 5-8 specific findings based on the actual values.
- Reference real numbers, percentages, and comparisons.

## Trends & Patterns
- Identify 3-5 meaningful patterns in the data.

## Anomalies & Concerns
- Flag any data quality issues or unusual values.

## Actionable Recommendations
- Provide 3-5 concrete, data-backed recommendations.

IMPORTANT: Do NOT describe the dataset structure. Analyze the actual VALUES."""

        analysis = ollama.invoke(prompt)

        return {
            "status": "success",
            "table_name": name,
            "kpis": kpis,
            "insights": analysis,
            "profile": profile,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dashboards/generate")
async def generate_dashboard(data: dict[str, Any]):
    try:
        warehouse = get_warehouse()
        builder = get_dashboard_builder()

        name = data.get("dataset_name")
        dashboard_type = data.get("dashboard_type", "auto")

        if not name:
            raise HTTPException(status_code=400, detail="dataset_name is required")

        df = warehouse.get_dataset(name)
        dashboard = builder.auto_dashboard(df, dashboard_type)

        kpis = dashboard.get("kpis", [])
        charts = dashboard.get("charts", {})
        charts_html = builder.to_html_dict(dashboard)

        chart_count = len([v for v in charts.values() if v is not None])

        return {
            "status": "success",
            "kpis": kpis,
            "charts_html": charts_html,
            "chart_count": chart_count,
            "dashboard_type": dashboard_type,
            "dataset_name": name,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboards")
async def list_dashboards():
    store = get_dashboard_store()
    dashboards = store.list_all()
    return {"dashboards": dashboards}


@app.get("/api/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: int):
    try:
        store = get_dashboard_store()
        dashboard = store.get_by_id(dashboard_id)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        return {"dashboard": dashboard}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/dashboards/{dashboard_id}")
async def delete_dashboard(dashboard_id: int):
    try:
        store = get_dashboard_store()
        store.delete(dashboard_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dashboards/save")
async def save_dashboard(data: dict[str, Any]):
    try:
        store = get_dashboard_store()
        name = data.get("name")
        dataset_name = data.get("dataset_name")
        dashboard_type = data.get("dashboard_type", "auto")
        kpis = data.get("kpis", [])
        charts_html = data.get("charts_html", {})

        if not name or not dataset_name:
            raise HTTPException(status_code=400, detail="name and dataset_name are required")

        store.save(
            name=name,
            dataset_name=dataset_name,
            dashboard_type=dashboard_type,
            kpis=kpis,
            charts_html=charts_html,
        )

        return {"status": "success", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reports/generate")
async def generate_report(data: dict[str, Any]):
    try:
        from app.etl.profiling import DataProfiling
        from app.etl.validation import DataValidation

        warehouse = get_warehouse()
        ollama = get_ollama_service()
        chart_eng = get_chart_engine()
        pipeline = get_etl_pipeline()
        report_gen = get_report_generator()

        name = data.get("dataset_name")
        title = data.get("title", "Analytics Report")
        format_type = data.get("format", "html")

        if not name:
            raise HTTPException(status_code=400, detail="dataset_name is required")

        df = warehouse.get_dataset(name)
        profile = DataProfiling.full_profile(df)
        validation = DataValidation.validate_dataset(df)
        kpis = chart_eng.generate_kpi_cards(df)
        history = pipeline.get_pipeline_history()

        prompt = f"""Generate an executive summary for a dataset with:
- {profile.get('overview', {}).get('rows', 0)} rows, {profile.get('overview', {}).get('columns', 0)} columns
- {profile.get('overview', {}).get('duplicate_pct', 0)}% duplicates
- Key columns: {list(profile.get('column_types', {}).keys())[:5]}

Write a professional 2-3 paragraph executive summary."""
        summary = ollama.invoke(prompt)

        insights_prompt = f"""Based on this data profile, list 5 specific business insights:
Profile: {profile}
Validation: {validation}"""
        insights_text = ollama.invoke(insights_prompt)
        insights = [l for l in insights_text.split("\n") if l.strip() and not l.startswith("#")][:5]

        recommendations_prompt = f"""Based on this data profile, provide 5 actionable recommendations:
Profile: {profile}
Insights: {insights}"""
        recs_text = ollama.invoke(recommendations_prompt)
        recommendations = [l for l in recs_text.split("\n") if l.strip() and not l.startswith("#")][:5]

        report_figures = chart_eng.generate_report_charts(df)
        charts_html = {}
        for chart_name, fig in report_figures.items():
            if fig is not None:
                charts_html[chart_name] = chart_eng.figure_to_html(fig)

        if format_type == "html":
            report = report_gen.generate_html_report(
                title, summary, kpis, insights, charts_html, history, recommendations
            )
        else:
            all_charts_flat = list(charts_html.values())
            report = report_gen.generate_markdown_report(
                title, summary, kpis, insights, all_charts_flat, history, recommendations
            )

        return {
            "status": "success",
            "report": report,
            "format": format_type,
            "chart_count": len(charts_html),
            "title": title,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitor/conversations")
async def get_conversations():
    mem = get_memory_manager()
    conversations = mem.get_conversation("main")
    return {"conversations": conversations}


@app.get("/api/monitor/context")
async def get_analytics_context():
    mem = get_memory_manager()
    ctx = mem.analytics_context
    cache = mem.schema_cache
    return {
        "analytics_context": ctx,
        "schema_cache": cache,
    }


frontend_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dir / "index.html"))
