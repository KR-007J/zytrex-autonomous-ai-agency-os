"""Multi-format enterprise export generator (CSV, XLSX, JSON, JSONL)."""

from __future__ import annotations
import io
import csv
import json
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


EXPORT_COLUMNS = [
    ("ID", "id"),
    ("Business Name", "business_name"),
    ("Domain", "domain"),
    ("Live Store URL", "canonical_url"),
    ("Primary Technology", "primary_technology"),
    ("Confidence", "technology_confidence"),
    ("Status", "status"),
    ("HTTP Status", "http_status"),
    ("SSL Active", "has_ssl"),
    ("Country", "country"),
    ("Industry", "industry"),
    ("Primary Email", "primary_email"),
    ("Primary Phone", "primary_phone"),
    ("Lead Score", "lead_score"),
    ("Score Rating", "score_label"),
    ("Score Reasons", "score_reasons"),
    ("Last Verified", "last_verified_at"),
]


class EnterpriseExporter:
    """Generates structured exports for enterprise analysis and CRM ingestion."""

    @classmethod
    def to_csv(cls, leads: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([col[0] for col in EXPORT_COLUMNS])

        for lead in leads:
            row = []
            for _, field in EXPORT_COLUMNS:
                val = lead.get(field)
                if isinstance(val, list):
                    val = " | ".join(str(v) for v in val)
                elif isinstance(val, bool):
                    val = "YES" if val else "NO"
                elif val is None:
                    val = ""
                row.append(val)
            writer.writerow(row)

        return output.getvalue()

    @classmethod
    def to_json(cls, leads: List[Dict[str, Any]], pretty: bool = True) -> str:
        return json.dumps(leads, indent=2 if pretty else None)

    @classmethod
    def to_jsonl(cls, leads: List[Dict[str, Any]]) -> str:
        return "\n".join(json.dumps(lead) for lead in leads)

    @classmethod
    def to_xlsx(cls, leads: List[Dict[str, Any]]) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "LeadForge Leads"

        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="0B0F1A", end_color="0B0F1A", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")

        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        # Write Header
        for col_idx, (col_name, _) in enumerate(EXPORT_COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border
            ws.row_dimensions[1].height = 28

        # Write Rows
        for row_idx, lead in enumerate(leads, start=2):
            ws.row_dimensions[row_idx].height = 22
            for col_idx, (_, field) in enumerate(EXPORT_COLUMNS, start=1):
                val = lead.get(field)
                if isinstance(val, list):
                    val = " | ".join(str(v) for v in val)
                elif isinstance(val, bool):
                    val = "YES" if val else "NO"
                elif val is None:
                    val = ""

                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = Font(name="Arial", size=10)
                cell.border = thin_border

                if field in ("lead_score", "id", "http_status"):
                    cell.alignment = Alignment(horizontal="center")
                elif field in ("status", "score_label"):
                    cell.alignment = Alignment(horizontal="center")
                    if val in ("HOT", "LIVE"):
                        cell.fill = PatternFill(start_color="DEF7EC", end_color="DEF7EC", fill_type="solid")
                        cell.font = Font(name="Arial", size=10, bold=True, color="03543F")

        # Auto adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
