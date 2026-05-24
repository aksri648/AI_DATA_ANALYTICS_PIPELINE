from pathlib import Path
from typing import Any

import pandas as pd

from app.config.settings import UPLOAD_DIR, SUPPORTED_FILE_TYPES
from app.db.duckdb_manager import duckdb_manager, quote_identifier
from app.utils.helpers import sanitize_table_name, generate_file_hash
from app.utils.logging import logger


class DataIngestion:
    @staticmethod
    def detect_file_type(file_path: str | Path) -> str:
        ext = Path(file_path).suffix.lower()
        if ext in (".xlsx", ".xls"):
            return "excel"
        if ext == ".csv":
            return "csv"
        if ext == ".json":
            return "json"
        if ext == ".parquet":
            return "parquet"
        if ext == ".pdf":
            return "pdf"
        raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def read_csv(file_path: str | Path, **kwargs) -> pd.DataFrame:
        kwargs.pop("sheet_name", None)
        return pd.read_csv(file_path, **kwargs)

    @staticmethod
    def read_excel(file_path: str | Path, sheet_name: str | int = 0, **kwargs) -> pd.DataFrame:
        return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)

    @staticmethod
    def read_json(file_path: str | Path, **kwargs) -> pd.DataFrame:
        return pd.read_json(file_path, **kwargs)

    @staticmethod
    def read_parquet(file_path: str | Path, **kwargs) -> pd.DataFrame:
        return pd.read_parquet(file_path, **kwargs)

    @staticmethod
    def read_file(file_path: str | Path, **kwargs) -> pd.DataFrame:
        ftype = DataIngestion.detect_file_type(file_path)
        if ftype == "pdf":
            raise ValueError("Use ingest_pdf() for PDF files — they produce multiple tables and text data")
        kwargs = dict(kwargs)
        readers = {
            "csv": DataIngestion.read_csv,
            "excel": DataIngestion.read_excel,
            "json": DataIngestion.read_json,
            "parquet": DataIngestion.read_parquet,
        }
        reader = readers.get(ftype)
        if not reader:
            raise ValueError(f"No reader for file type: {ftype}")
        # Only pass sheet_name to Excel reader
        if ftype != "excel" and "sheet_name" in kwargs:
            kwargs.pop("sheet_name")
        return reader(file_path, **kwargs)

    @staticmethod
    def infer_schema(df: pd.DataFrame) -> list[dict[str, Any]]:
        schema = []
        for col in df.columns:
            dtype = df[col].dtype
            col_info = {
                "name": col,
                "dtype": str(dtype),
                "nullable": bool(df[col].isnull().any()),
                "unique_count": int(df[col].nunique()),
                "null_count": int(df[col].isnull().sum()),
                "sample_values": df[col].dropna().head(3).tolist(),
            }
            if pd.api.types.is_numeric_dtype(dtype):
                col_info["min"] = float(df[col].min()) if df[col].notna().any() else None
                col_info["max"] = float(df[col].max()) if df[col].notna().any() else None
            schema.append(col_info)
        return schema

    @staticmethod
    def ingest_file(
        file_path: str | Path, table_name: str | None = None, sheet_name: str | int = 0
    ) -> dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        name = sanitize_table_name(table_name or file_path.stem)
        df = DataIngestion.read_file(file_path, sheet_name=sheet_name)

        duckdb_manager.register_table(df, name)

        metadata = {
            "source": str(file_path),
            "table_name": name,
            "rows": len(df),
            "columns": len(df.columns),
            "file_hash": generate_file_hash(file_path),
            "schema": DataIngestion.infer_schema(df),
        }
        meta_df = pd.DataFrame([metadata])
        duckdb_manager.register_table(meta_df, f"{name}_metadata", replace=True)

        logger.info(f"Ingested {len(df)} rows into '{name}'")
        return metadata

    @staticmethod
    def ingest_pdf(
        file_path: str | Path, table_name: str | None = None
    ) -> dict[str, Any]:
        """Ingest a PDF: extract tables as structured data and text as JSON interface."""
        from app.etl.pdf_parser import pdf_parser

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        name = sanitize_table_name(table_name or file_path.stem)
        parsed = pdf_parser.parse_pdf(file_path)

        tables = parsed["tables"]
        text_pages = parsed["text_pages"]
        sections = parsed["sections"]
        figures = parsed["figures"]
        ingested_tables = []

        # 1. Ingest each extracted table
        for i, tbl_df in enumerate(tables):
            tbl_name = f"{name}_table_{i + 1}"
            duckdb_manager.register_table(tbl_df, tbl_name)
            ingested_tables.append({
                "table_name": tbl_name,
                "rows": len(tbl_df),
                "columns": len(tbl_df.columns),
                "source_page": tbl_df.attrs.get("source_page"),
                "column_names": tbl_df.columns.tolist(),
            })
            logger.info(f"  Extracted table '{tbl_name}': {len(tbl_df)} rows")

        # 2. Ingest text pages as JSON interface
        if text_pages:
            text_df = pd.DataFrame(text_pages)
            text_tbl_name = f"{name}_text"
            duckdb_manager.register_table(text_df, text_tbl_name)
            ingested_tables.append({
                "table_name": text_tbl_name,
                "rows": len(text_df),
                "columns": len(text_df.columns),
                "type": "text_pages",
            })

        # 3. Ingest sections as structured text
        if sections:
            sec_df = pd.DataFrame(sections)
            if "content" in sec_df.columns:
                sec_df = sec_df.drop(columns=["content"])
            sec_tbl_name = f"{name}_sections"
            duckdb_manager.register_table(sec_df, sec_tbl_name)
            ingested_tables.append({
                "table_name": sec_tbl_name,
                "rows": len(sec_df),
                "type": "sections",
            })

        # 4. Ingest financial figures if found
        if not figures.empty:
            fig_tbl_name = f"{name}_figures"
            duckdb_manager.register_table(figures, fig_tbl_name)
            ingested_tables.append({
                "table_name": fig_tbl_name,
                "rows": len(figures),
                "type": "financial_figures",
            })

        # 5. Store full document text as single-row JSON
        doc_meta = pd.DataFrame([{
            "file_name": file_path.name,
            "total_pages": parsed["pages"],
            "tables_found": len(tables),
            "sections_found": len(sections),
            "figures_found": len(figures),
            "full_text": parsed["full_text"],
        }])
        doc_tbl_name = f"{name}_document"
        duckdb_manager.register_table(doc_meta, doc_tbl_name)

        metadata = {
            "source": str(file_path),
            "source_type": "pdf",
            "table_name": name,
            "pages": parsed["total_pages"],
            "pages_with_text": parsed["pages_with_text"],
            "tables_extracted": len(tables),
            "sections_extracted": len(sections),
            "figures_extracted": len(figures),
            "is_scanned": parsed.get("is_scanned", False),
            "ocr_pages_used": parsed.get("ocr_pages_used", 0),
            "ingested_tables": ingested_tables,
            "file_hash": generate_file_hash(file_path),
        }
        meta_df = pd.DataFrame([metadata])
        duckdb_manager.register_table(meta_df, f"{name}_metadata", replace=True)

        logger.info(f"PDF ingested: {len(tables)} tables, {len(sections)} sections, {len(figures)} figures")
        return metadata

    @staticmethod
    def ingest_df(df: pd.DataFrame, table_name: str) -> dict[str, Any]:
        name = sanitize_table_name(table_name)
        duckdb_manager.register_table(df, name)

        metadata = {
            "source": "dataframe",
            "table_name": name,
            "rows": len(df),
            "columns": len(df.columns),
            "file_hash": None,
            "schema": DataIngestion.infer_schema(df),
        }
        meta_df = pd.DataFrame([metadata])
        duckdb_manager.register_table(meta_df, f"{name}_metadata", replace=True)

        logger.info(f"Ingested {len(df)} rows into '{name}'")
        return metadata

    @staticmethod
    def list_excel_sheets(file_path: str | Path) -> list[str]:
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names

    @staticmethod
    def get_preview(table_name: str, n: int = 10) -> pd.DataFrame:
        table_name = sanitize_table_name(table_name)
        return duckdb_manager.query(f"SELECT * FROM {quote_identifier(table_name)} LIMIT {n}")
