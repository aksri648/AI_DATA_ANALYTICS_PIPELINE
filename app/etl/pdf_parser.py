import re
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from app.utils.logging import logger


class PDFParser:
    """Extract tables and text from PDF documents for analytics, with OCR fallback for scanned PDFs."""

    def __init__(self):
        self._ocr_engine = None

    def _get_ocr_engine(self):
        if self._ocr_engine is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._ocr_engine = RapidOCR()
                logger.info("RapidOCR engine loaded for PDF OCR")
            except ImportError:
                logger.warning("RapidOCR not available — OCR disabled")
                self._ocr_engine = False
        return self._ocr_engine if self._ocr_engine is not False else None

    @staticmethod
    def extract_tables(file_path: str | Path) -> list[pd.DataFrame]:
        """Extract all tables from a PDF as a list of DataFrames."""
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = page.extract_tables()
                for table_data in page_tables:
                    if not table_data or len(table_data) < 2:
                        continue
                    header = table_data[0]
                    header = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header)]
                    header = PDFParser._deduplicate_headers(header)
                    rows = table_data[1:]
                    df = pd.DataFrame(rows, columns=header)
                    df = PDFParser._clean_table_df(df)
                    if not df.empty:
                        df.attrs["source_page"] = page_num
                        tables.append(df)
        return tables

    @staticmethod
    def _deduplicate_headers(headers: list[str]) -> list[str]:
        seen: dict[str, int] = {}
        result = []
        for h in headers:
            if h in seen:
                seen[h] += 1
                result.append(f"{h}_{seen[h]}")
            else:
                seen[h] = 0
                result.append(h)
        return result

    @staticmethod
    def _clean_table_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(how="all")
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        for col in df.columns:
            try:
                converted = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce")
                if converted.notna().sum() > len(df) * 0.5:
                    df[col] = converted
            except (ValueError, TypeError):
                pass
        return df

    def ocr_pages(self, file_path: str | Path, dpi: int = 300) -> list[dict[str, Any]]:
        """Convert PDF pages to images and run OCR on each page."""
        engine = self._get_ocr_engine()
        if engine is None:
            logger.warning("OCR engine not available — skipping OCR")
            return []

        from pdf2image import convert_from_path
        logger.info(f"Running OCR on {file_path} (dpi={dpi})")
        pages = []
        try:
            images = convert_from_path(str(file_path), dpi=dpi)
        except Exception as e:
            logger.error(f"pdf2image failed: {e}")
            return []

        for page_num, img in enumerate(images, 1):
            import numpy as np
            img_array = np.array(img)
            result, _ = engine(img_array)
            if result:
                text_parts = [item[1] for item in result]
                text = "\n".join(text_parts)
                confidence = sum(item[2] for item in result) / len(result) if result else 0
            else:
                text = ""
                confidence = 0
            pages.append({
                "page": page_num,
                "text": text.strip(),
                "char_count": len(text.strip()),
                "ocr_confidence": round(confidence, 2),
                "source": "ocr",
            })
            logger.debug(f"  Page {page_num}: {len(text)} chars, confidence={confidence:.2f}")
        logger.info(f"OCR complete: {len(pages)} pages processed")
        return pages

    @staticmethod
    def extract_text(file_path: str | Path) -> list[dict[str, Any]]:
        """Extract embedded text from each page using pdfplumber."""
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    pages.append({
                        "page": page_num,
                        "text": text,
                        "char_count": len(text),
                        "source": "embedded",
                    })
        return pages

    def extract_text_with_ocr_fallback(self, file_path: str | Path, ocr_threshold: int = 50) -> list[dict[str, Any]]:
        """Extract text from PDF, falling back to OCR for pages with no embedded text."""
        embedded = PDFParser.extract_text(file_path)
        embedded_by_page = {p["page"]: p for p in embedded}

        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)

        # Identify pages that need OCR (fewer than ocr_threshold chars)
        pages_needing_ocr = []
        for pg in range(1, total_pages + 1):
            entry = embedded_by_page.get(pg)
            if not entry or entry["char_count"] < ocr_threshold:
                pages_needing_ocr.append(pg)

        if not pages_needing_ocr:
            logger.info(f"All {total_pages} pages have embedded text — no OCR needed")
            return embedded

        logger.info(f"{len(pages_needing_ocr)} of {total_pages} pages need OCR (threshold={ocr_threshold} chars)")
        ocr_results = self.ocr_pages(file_path)
        ocr_by_page = {p["page"]: p for p in ocr_results}

        final: list[dict[str, Any]] = []
        for pg in range(1, total_pages + 1):
            entry = embedded_by_page.get(pg)
            if entry and entry["char_count"] >= ocr_threshold:
                final.append(entry)
            elif pg in ocr_by_page and ocr_by_page[pg]["text"]:
                ocr_entry = ocr_by_page[pg]
                ocr_entry["page"] = pg
                final.append(ocr_entry)
            else:
                final.append({"page": pg, "text": "", "char_count": 0, "source": "empty"})
        return final

    @staticmethod
    def is_scanned_pdf(file_path: str | Path, threshold: int = 50) -> bool:
        """Detect if a PDF is scanned (minimal embedded text on most pages)."""
        with pdfplumber.open(file_path) as pdf:
            total = len(pdf.pages)
            empty = 0
            for page in pdf.pages:
                text = (page.extract_text() or "").strip()
                if len(text) < threshold:
                    empty += 1
        ratio = empty / total if total else 0
        return ratio > 0.5

    @staticmethod
    def extract_sections(text_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract text and attempt to identify section headings from parsed pages."""
        sections = []
        heading_pattern = re.compile(
            r"^(?:(?:\d+\.?\s+)|(?:[A-Z][A-Z\s]{3,})|(?:Chapter\s+\d+)|(?:Section\s+\d+))",
            re.MULTILINE,
        )
        for page_info in text_pages:
            text = page_info.get("text", "")
            page_num = page_info.get("page", 0)
            if not text:
                continue
            lines = text.split("\n")
            current_section = {"page": page_num, "heading": "", "content": []}
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                if heading_pattern.match(stripped) and len(stripped) < 120:
                    if current_section["content"]:
                        current_section["text"] = "\n".join(current_section["content"])
                        sections.append(current_section)
                    current_section = {
                        "page": page_num,
                        "heading": stripped,
                        "content": [],
                    }
                else:
                    current_section["content"].append(stripped)
            if current_section["content"]:
                current_section["text"] = "\n".join(current_section["content"])
                sections.append(current_section)
        return sections

    @staticmethod
    def extract_financial_figures(text_pages: list[dict[str, Any]]) -> pd.DataFrame:
        """Try to extract financial figures (number patterns) from text."""
        records = []
        figure_pattern = re.compile(
            r"(?P<label>[A-Za-z][A-Za-z\s&/'-]{2,60}?)\s*[:\-]?\s*"
            r"(?:Rs\.?|₹|\$|EUR|GBP)?\s*"
            r"(?P<value>[\d,]+(?:\.\d+)?)\s*"
            r"(?P<unit>crores?|lakhs?|millions?|billions?|mn|bn|cr)?",
            re.IGNORECASE,
        )
        for page_info in text_pages:
            for match in figure_pattern.finditer(page_info.get("text", "")):
                label = match.group("label").strip()
                value_str = match.group("value").replace(",", "")
                try:
                    value = float(value_str)
                except ValueError:
                    continue
                if value == 0 or len(label) < 3:
                    continue
                records.append({
                    "page": page_info.get("page", 0),
                    "label": label.strip(),
                    "value": value,
                    "unit": (match.group("unit") or "").lower(),
                })
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df = df.drop_duplicates(subset=["label", "value"])
        return df

    def parse_pdf(self, file_path: str | Path, use_ocr: bool = True) -> dict[str, Any]:
        """Full PDF parsing: tables, text (with OCR fallback), sections, financial figures."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info(f"Parsing PDF: {file_path.name}")
        is_scanned = PDFParser.is_scanned_pdf(file_path)
        if is_scanned:
            logger.info("PDF appears to be scanned — will use OCR for text extraction")

        tables = PDFParser.extract_tables(file_path)

        if use_ocr and (is_scanned or self._get_ocr_engine()):
            text_pages = self.extract_text_with_ocr_fallback(file_path)
        else:
            text_pages = PDFParser.extract_text(file_path)

        sections = PDFParser.extract_sections(text_pages)
        figures = PDFParser.extract_financial_figures(text_pages)

        ocr_pages_used = sum(1 for p in text_pages if p.get("source") == "ocr")

        result = {
            "file": str(file_path),
            "total_pages": len(text_pages),
            "pages_with_text": sum(1 for p in text_pages if p.get("char_count", 0) > 0),
            "tables": tables,
            "tables_count": len(tables),
            "text_pages": text_pages,
            "sections": sections,
            "figures": figures,
            "full_text": "\n\n".join(p.get("text", "") for p in text_pages),
            "is_scanned": is_scanned,
            "ocr_pages_used": ocr_pages_used,
        }
        logger.info(
            f"PDF parsed: {result['total_pages']} pages, {len(tables)} tables, "
            f"{len(sections)} sections, {len(figures)} figures, "
            f"scanned={is_scanned}, ocr_pages={ocr_pages_used}"
        )
        return result


pdf_parser = PDFParser()
