"""Asynchronous Job Manager executing discovery, verification, and lead enrichment."""

from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set
from src.database.db import get_db
from src.database.models import DiscoveryJob, Lead
from src.database.repository import LeadRepository
from src.discovery.orchestrator import orchestrator
from src.verification.live_verifier import LiveVerifier
from src.fingerprint.engine import FingerprintEngine
from src.crawler.contact_extractor import ContactExtractor
from src.scoring.lead_scorer import LeadScorer
from src.jobs.sse import broadcaster


class JobManager:
    """Coordinates async worker pipelines and updates jobs table."""

    @classmethod
    async def start_discovery_job(
        cls,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        require_email: bool = False,
        limit: int = 20,
        replace_existing: bool = False,
    ) -> str:
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        with get_db() as session:
            job = DiscoveryJob(
                id=job_id,
                technology=technology,
                country=country,
                industry=industry,
                status="RUNNING",
                progress_percent=0,
                candidates_count=0,
                verified_count=0,
                qualified_count=0,
                created_at=now,
            )
            session.add(job)

        # Launch worker in background task
        asyncio.create_task(
            cls._execute_discovery_pipeline(
                job_id=job_id,
                technology=technology,
                country=country,
                industry=industry,
                require_email=require_email,
                limit=limit,
                replace_existing=replace_existing,
            )
        )
        return job_id

    @classmethod
    async def _execute_discovery_pipeline(
        cls,
        job_id: str,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        require_email: bool = False,
        limit: int = 20,
        replace_existing: bool = False,
    ) -> None:
        candidates: List[str] = []
        verified_count = 0
        qualified_count = 0
        processed_count = 0
        old_domains: Set[str] = set()

        old_domains = set()
        if replace_existing:
            with get_db() as session:
                session.query(Lead).delete()
                session.commit()
        else:
            with get_db() as session:
                old_domains = {r[0] for r in session.query(Lead.domain).all()}

        # Concurrent verification worker pool with Semaphore(25)
        sem = asyncio.Semaphore(25)
        lock = asyncio.Lock()
        tasks: List[asyncio.Task] = []

        async def verify_and_process(domain: str):
            nonlocal verified_count, qualified_count, processed_count
            try:
                async with sem:
                    v_res = await LiveVerifier.verify(domain, timeout=3.5)

                    detected_techs = []
                    primary_tech = None
                    tech_confidence = 0.0
                    evidence_list = []
                    extracted_contacts = {"emails": [], "phones": [], "socials": {}}

                    if v_res.is_live:
                        detections = FingerprintEngine.detect(
                            html=v_res.html_body,
                            headers=v_res.headers,
                            cookies=v_res.cookies,
                            target_tech_id=technology.lower(),
                        )
                        detected_techs = [d.to_dict() for d in detections]
                        if detections:
                            top = detections[0]
                            primary_tech = top.name
                            tech_confidence = top.confidence
                            evidence_list = top.evidence
                        else:
                            primary_tech = "Web Standard"
                            tech_confidence = 0.4
                            evidence_list = ["Standard web server detected"]

                        extracted = ContactExtractor.extract_from_html(v_res.html_body, v_res.canonical_url)
                        extracted_contacts = extracted

                    has_tech_match = primary_tech and technology.lower() in primary_tech.lower()
                    score_res = LeadScorer.calculate(
                        has_tech_match=bool(has_tech_match),
                        tech_confidence=tech_confidence,
                        target_country_match=True if country else False,
                        target_industry_match=True if industry else False,
                        has_public_email=len(extracted_contacts.get("emails", [])) > 0,
                        has_public_phone=len(extracted_contacts.get("phones", [])) > 0,
                        has_ssl=v_res.has_ssl,
                        response_time_ms=v_res.response_time_ms,
                        is_live=v_res.is_live,
                        freshness_status=v_res.freshness_status,
                        tech_name=primary_tech or technology,
                    )

                    async with lock:
                        if v_res.is_live:
                            verified_count += 1
                        is_qualified = score_res.score >= 50 and (not require_email or len(extracted_contacts.get("emails", [])) > 0)
                        if is_qualified:
                            qualified_count += 1
                        processed_count += 1
                        curr_total = max(len(candidates), 1)
                        progress_pct = min(int((processed_count / curr_total) * 100), 99)

                        with get_db() as session:
                            lead, created = LeadRepository.upsert_lead(
                                session=session,
                                domain=domain,
                                canonical_url=v_res.canonical_url,
                                business_name=extracted_contacts.get("business_name") or domain,
                                description=extracted_contacts.get("description"),
                                country=country or "United Kingdom",
                                region="Europe",
                                industry=industry or "E-commerce",
                                status="LIVE" if v_res.is_live else "OFFLINE",
                                http_status=v_res.http_status,
                                has_ssl=v_res.has_ssl,
                                response_time_ms=v_res.response_time_ms,
                                primary_technology=primary_tech,
                                technology_category="E-Commerce",
                                technology_confidence=tech_confidence,
                                evidence=evidence_list,
                                technologies=detected_techs,
                                emails=extracted_contacts.get("emails", []),
                                phones=extracted_contacts.get("phones", []),
                                socials=extracted_contacts.get("socials", {}),
                                lead_score=score_res.score,
                                score_label=score_res.label,
                                score_reasons=score_res.reasons,
                                source="LIVE_CRAWL",
                            )
                            lead_data = lead.to_dict()

                            job = session.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
                            if job:
                                job.progress_percent = progress_pct
                                job.verified_count = verified_count
                                job.qualified_count = qualified_count

                        # Broadcast SSE lead processed event immediately to UI
                        await broadcaster.publish(
                            job_id,
                            {
                                "event": "LEAD_PROCESSED",
                                "progress": progress_pct,
                                "lead": lead_data,
                                "verified_count": verified_count,
                                "qualified_count": qualified_count,
                            },
                        )
            except Exception as domain_err:
                print(f"Error processing domain {domain}: {domain_err}")
                async with lock:
                    processed_count += 1

        # Stream candidate domains and immediately dispatch verification concurrently
        async for candidate in orchestrator.stream_candidates(
            technology=technology, country=country, industry=industry, limit=limit, exclude_domains=old_domains
        ):
            candidates.append(candidate.domain)

            with get_db() as session:
                job = session.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
                if job:
                    job.candidates_count = len(candidates)

            # Update job progress
            await broadcaster.publish(
                job_id,
                {
                    "event": "CANDIDATE_DISCOVERED",
                    "domain": candidate.domain,
                    "source": candidate.source,
                    "count": len(candidates),
                },
            )

            # Launch verification worker immediately in background (Producer-Consumer)
            tasks.append(asyncio.create_task(verify_and_process(candidate.domain)))

            if qualified_count >= limit:
                break

        # Await remaining in-flight verification tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        total_candidates = len(candidates)
        if total_candidates == 0:
            with get_db() as session:
                job = session.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
                if job:
                    job.status = "COMPLETED"
                    job.completed_at = datetime.now(timezone.utc)
            await broadcaster.publish(
                job_id,
                {
                    "event": "JOB_COMPLETED",
                    "status": "COMPLETED",
                    "message": "No new candidates found for criteria.",
                    "job_id": job_id,
                    "candidates_count": 0,
                    "verified_count": 0,
                    "qualified_count": 0,
                },
            )
            return

        # Mark job completed
        with get_db() as session:
            job = session.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
            if job:
                job.status = "COMPLETED"
                job.progress_percent = 100
                job.candidates_count = total_candidates
                job.verified_count = verified_count
                job.qualified_count = qualified_count
                job.completed_at = datetime.now(timezone.utc)

        await broadcaster.publish(
            job_id,
            {
                "event": "JOB_COMPLETED",
                "status": "COMPLETED",
                "message": f"Discovery complete. {qualified_count} qualified leads verified live from {total_candidates} candidates.",
                "job_id": job_id,
                "candidates_count": total_candidates,
                "verified_count": verified_count,
                "qualified_count": qualified_count,
            },
        )

    @classmethod
    async def refresh_lead(cls, lead_id: int) -> Optional[Dict[str, Any]]:
        """Re-verify, re-fingerprint, re-extract contacts, and re-score an existing lead."""
        with get_db() as session:
            lead = LeadRepository.get_lead_by_id(session, lead_id)
            if not lead:
                return None
            domain = lead.domain
            country = lead.country
            industry = lead.industry

        v_res = await LiveVerifier.verify(domain, timeout=10.0)
        detected_techs = []
        primary_tech = "Unknown"
        tech_confidence = 0.0
        evidence_list = []
        extracted_contacts = {"emails": [], "phones": [], "socials": {}}

        if v_res.is_live:
            detections = FingerprintEngine.detect(
                html=v_res.html_body,
                headers=v_res.headers,
                cookies=v_res.cookies,
            )
            detected_techs = [d.to_dict() for d in detections]
            if detections:
                top = detections[0]
                primary_tech = top.name
                tech_confidence = top.confidence
                evidence_list = top.evidence

            extracted = ContactExtractor.extract_from_html(v_res.html_body, v_res.canonical_url)
            extracted_contacts = extracted

        score_res = LeadScorer.calculate(
            has_tech_match=tech_confidence >= 0.5,
            tech_confidence=tech_confidence,
            target_country_match=bool(country),
            target_industry_match=bool(industry),
            has_public_email=len(extracted_contacts.get("emails", [])) > 0,
            has_public_phone=len(extracted_contacts.get("phones", [])) > 0,
            has_ssl=v_res.has_ssl,
            response_time_ms=v_res.response_time_ms,
            is_live=v_res.is_live,
            freshness_status=v_res.freshness_status,
            tech_name=primary_tech,
        )

        with get_db() as session:
            updated_lead, _ = LeadRepository.upsert_lead(
                session=session,
                domain=domain,
                canonical_url=v_res.canonical_url,
                business_name=extracted_contacts.get("business_name") or domain,
                description=extracted_contacts.get("description"),
                country=country,
                industry=industry,
                status="LIVE" if v_res.is_live else "OFFLINE",
                http_status=v_res.http_status,
                has_ssl=v_res.has_ssl,
                response_time_ms=v_res.response_time_ms,
                primary_technology=primary_tech,
                technology_confidence=tech_confidence,
                evidence=evidence_list,
                technologies=detected_techs,
                emails=extracted_contacts.get("emails", []),
                phones=extracted_contacts.get("phones", []),
                socials=extracted_contacts.get("socials", {}),
                lead_score=score_res.score,
                score_label=score_res.label,
                score_reasons=score_res.reasons,
                source="REFRESH_JOB",
            )
            return updated_lead.to_dict()
