"""Asynchronous Export Execution Manager."""

from __future__ import annotations
import asyncio
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.database.db import get_db
from src.database.models import ExportJob
from src.database.repository import LeadRepository
from src.export.exporter import EnterpriseExporter
from src.config import PROJECT_ROOT


EXPORTS_DIR = PROJECT_ROOT / "data" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


class AsyncExportManager:
    """Coordinates asynchronous background export tasks and tracks status via ExportJob."""

    @classmethod
    def start_export_job(
        cls,
        export_format: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5000,
    ) -> str:
        job_id = f"exp_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        fmt_clean = export_format.upper().strip()
        filters = filters or {}

        with get_db() as session:
            job = ExportJob(
                id=job_id,
                format=fmt_clean,
                status="PENDING",
                filters_json=json.dumps(filters),
                created_at=now,
            )
            session.add(job)

        # Trigger execution in background task
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(cls._execute_export(job_id, fmt_clean, filters, limit))
        except RuntimeError:
            # If called from a synchronous context without a running loop
            asyncio.run(cls._execute_export(job_id, fmt_clean, filters, limit))

        return job_id

    @classmethod
    async def _execute_export(
        cls,
        job_id: str,
        export_format: str,
        filters: Dict[str, Any],
        limit: int = 5000,
    ) -> None:
        # Mark status as PROCESSING
        with get_db() as session:
            job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
            if job:
                job.status = "PROCESSING"

        try:
            # Query leads
            with get_db() as session:
                leads, _ = LeadRepository.query_leads(
                    session=session,
                    technology=filters.get("technology"),
                    country=filters.get("country"),
                    industry=filters.get("industry"),
                    status=filters.get("status"),
                    has_email=filters.get("has_email"),
                    min_score=filters.get("min_score"),
                    query=filters.get("query"),
                    limit=limit,
                )
                raw_leads = [l.to_dict() for l in leads]

            # Generate export data and determine extension
            fmt = export_format.lower()
            if fmt == "csv":
                ext = "csv"
                content = EnterpriseExporter.to_csv(raw_leads).encode("utf-8")
            elif fmt == "xlsx":
                ext = "xlsx"
                content = EnterpriseExporter.to_xlsx(raw_leads)
            elif fmt == "json":
                ext = "json"
                content = EnterpriseExporter.to_json(raw_leads).encode("utf-8")
            elif fmt == "jsonl":
                ext = "jsonl"
                content = EnterpriseExporter.to_jsonl(raw_leads).encode("utf-8")
            elif fmt == "parquet":
                ext = "parquet"
                content = EnterpriseExporter.to_parquet(raw_leads)
            elif fmt in ("md", "markdown"):
                ext = "md"
                content = EnterpriseExporter.to_markdown(raw_leads).encode("utf-8")
            elif fmt == "pdf":
                ext = "pdf"
                content = EnterpriseExporter.to_pdf(raw_leads)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            # Persist file
            out_file = EXPORTS_DIR / f"{job_id}.{ext}"
            out_file.write_bytes(content)

            # Update job record
            now = datetime.now(timezone.utc)
            with get_db() as session:
                job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
                if job:
                    job.status = "COMPLETED"
                    job.file_path = str(out_file)
                    job.file_size = len(content)
                    job.total_records = len(raw_leads)
                    job.completed_at = now

            # Attempt webhook dispatch for export.completed
            try:
                from src.webhooks.dispatcher import WebhookDispatcher
                asyncio.create_task(
                    WebhookDispatcher.dispatch(
                        "export.completed",
                        {
                            "job_id": job_id,
                            "format": export_format,
                            "records_count": len(raw_leads),
                            "file_size": len(content),
                            "file_path": str(out_file),
                        },
                    )
                )
            except Exception:
                pass

        except Exception as exc:
            now = datetime.now(timezone.utc)
            with get_db() as session:
                job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
                if job:
                    job.status = "FAILED"
                    job.error_message = str(exc)
                    job.completed_at = now

    @classmethod
    def get_export_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as session:
            job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
            return job.to_dict() if job else None

    @classmethod
    def list_export_jobs(cls, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db() as session:
            jobs = (
                session.query(ExportJob)
                .order_by(ExportJob.created_at.desc())
                .limit(limit)
                .all()
            )
            return [j.to_dict() for j in jobs]
