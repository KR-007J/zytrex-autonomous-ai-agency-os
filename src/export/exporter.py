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
    def sanitize_spreadsheet_value(cls, val: Any) -> Any:
        """Sanitize tabular outputs to prevent spreadsheet formula injection.

        Prepends a single quote `'` to any string starting with '=', '+', '-', '@'.
        """
        if isinstance(val, str) and val.startswith(("=", "+", "-", "@")):
            return f"'{val}"
        return val

    # Direct alias
    sanitize_formula_injection = sanitize_spreadsheet_value

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
                # Prevent spreadsheet formula injection
                val = cls.sanitize_spreadsheet_value(val)
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

                # Prevent spreadsheet formula injection
                val = cls.sanitize_spreadsheet_value(val)

                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = Font(name="Arial", size=10)
                cell.border = thin_border

                if field in ("lead_score", "id", "http_status"):
                    cell.alignment = Alignment(horizontal="center")
                elif field in ("status", "score_label"):
                    cell.alignment = Alignment(horizontal="center")
                    if str(val) in ("HOT", "LIVE"):
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

    @classmethod
    def to_markdown(cls, leads: List[Dict[str, Any]]) -> str:
        """Export leads to a GitHub-flavored Markdown table."""
        headers = ["ID", "Business Name", "Domain", "Primary Tech", "Status", "Country", "Email", "Score", "Rating"]
        keys = ["id", "business_name", "domain", "primary_technology", "status", "country", "primary_email", "lead_score", "score_label"]

        lines = [
            f"| {' | '.join(headers)} |",
            f"| {' | '.join(['---'] * len(headers))} |"
        ]
        for lead in leads:
            row = []
            for k in keys:
                v = lead.get(k)
                if v is None:
                    v = ""
                # Escape pipe character to preserve markdown table formatting
                row.append(str(v).replace("|", "\\|"))
            lines.append(f"| {' | '.join(row)} |")
        return "\n".join(lines)

    @classmethod
    def to_parquet(cls, leads: List[Dict[str, Any]]) -> bytes:
        """Export leads to Apache Parquet format.

        Uses pyarrow or fastparquet if installed; falls back to gzip-compressed JSONL.
        """
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq

            records = []
            for lead in leads:
                rec = {}
                for k, v in lead.items():
                    if isinstance(v, (list, dict)):
                        rec[k] = json.dumps(v)
                    else:
                        rec[k] = v
                records.append(rec)
            table = pa.Table.from_pylist(records)
            buf = io.BytesIO()
            pq.write_table(table, buf)
            return buf.getvalue()
        except ImportError:
            try:
                import fastparquet  # type: ignore
                import pandas as pd  # type: ignore
                df = pd.DataFrame(leads)
                buf = io.BytesIO()
                df.to_parquet(buf, engine="fastparquet")
                return buf.getvalue()
            except ImportError:
                import gzip
                jsonl_bytes = cls.to_jsonl(leads).encode("utf-8")
                return gzip.compress(jsonl_bytes)

    @classmethod
    def to_pdf(cls, leads: List[Dict[str, Any]]) -> bytes:
        """Export leads to a styled PDF intelligence document using ReportLab."""
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0B0F1A"),
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4B5563"),
        )
        cell_style = ParagraphStyle(
            "CellText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1F2937"),
        )
        header_style = ParagraphStyle(
            "HeaderCellText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )

        elements = []
        elements.append(Paragraph("LeadForge — Lead Intelligence Report", title_style))
        elements.append(Paragraph(f"Total Qualified Records: {len(leads)}", subtitle_style))
        elements.append(Spacer(1, 12))

        pdf_cols = [
            ("Business Name", "business_name"),
            ("Domain", "domain"),
            ("Primary Tech", "primary_technology"),
            ("Status", "status"),
            ("Country", "country"),
            ("Email", "primary_email"),
            ("Score", "lead_score"),
            ("Rating", "score_label"),
        ]

        header_row = [Paragraph(col[0], header_style) for col in pdf_cols]
        table_data = [header_row]

        for lead in leads:
            row = []
            for _, field in pdf_cols:
                val = lead.get(field)
                if val is None:
                    val = ""
                row.append(Paragraph(str(val), cell_style))
            table_data.append(row)

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B0F1A")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                    ("TOPPADDING", (0, 0), (-1, 0), 5),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("TOPPADDING", (0, 1), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ]
            )
        )
        elements.append(table)
        doc.build(elements)
        return buf.getvalue()

