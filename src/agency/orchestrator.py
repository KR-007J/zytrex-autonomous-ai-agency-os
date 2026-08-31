"""Autonomous AI Agency Orchestrator — End-to-End Hands-Free Automation."""

from __future__ import annotations
import time
import threading
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from collections import deque

from src.config import RootConfig, load_config
from src.database.db import get_db_session, LeadRepository
from src.database.models import Lead, ScrapeJob, OutreachDraft, ContactedMemory
from src.scraper.agency_engine import AgencyLeadDiscoveryEngine, US_REGIONS, TARGET_NICHES, INTENT_CATEGORIES
from src.scraper.google_engine import GoogleAutonomousLeadEngine
from src.outreach.email_engine import ColdEmailEngine
from src.export.excel_generator import ExcelReportGenerator
from src.notifications.notifier import NotificationDispatcher

logger = logging.getLogger("leadgen.orchestrator")


class AutonomousAgencyOrchestrator:
    _instance: Optional[AutonomousAgencyOrchestrator] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AutonomousAgencyOrchestrator, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[RootConfig] = None):
        if getattr(self, "_initialized", False):
            return
        self.config = config or load_config()
        self.agency_engine = AgencyLeadDiscoveryEngine(self.config)
        self.google_engine = GoogleAutonomousLeadEngine()
        self.emailer = ColdEmailEngine(self.config)
        self.excel_gen = ExcelReportGenerator()
        self.notifier = NotificationDispatcher(self.config)

        self.is_running = True  # Default to active autopilot
        self.interval_seconds = 1800  # Run every 30 minutes
        self.auto_email = True
        self.dry_run = True  # Safety dry-run by default until SMTP configured
        self.current_region_index = 0
        self.current_niche_index = 0

        self.cycles_completed = 0
        self.last_cycle_at: Optional[datetime] = None
        self.total_leads_scouted = 0
        self.total_emails_sent = 0
        self.latest_excel_path: Optional[str] = None

        # Live activity log queue (keeps last 100 event strings)
        self.activity_logs: deque[Dict[str, Any]] = deque(maxlen=100)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = True

        self.log_activity("SYSTEM", "Autonomous AI Agency Orchestrator initialized and ready.")

    def log_activity(self, action_type: str, message: str) -> None:
        """Record real-time activity event for the executive mission control."""
        event = {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "type": action_type,  # SCOUT, ENRICH, EMAIL, EXPORT, SYSTEM
            "message": message,
        }
        self.activity_logs.appendleft(event)
        logger.info(f"[{action_type}] {message}")

    def start_autopilot(self, interval_seconds: int = 1800, auto_email: bool = True, dry_run: bool = True) -> bool:
        """Start the hands-free 24/7 agency autopilot loop."""
        with self._lock:
            self.interval_seconds = interval_seconds
            self.auto_email = auto_email
            self.dry_run = dry_run
            self.is_running = True
            self._stop_event.clear()

            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._autopilot_loop, daemon=True, name="AgencyAutopilotDaemon")
                self._thread.start()

            self.log_activity("SYSTEM", f"🟢 24/7 Autonomous Autopilot Activated (Interval: {interval_seconds}s, Auto-Email: {auto_email}).")
            return True

    def stop_autopilot(self) -> bool:
        """Pause the autonomous autopilot loop."""
        with self._lock:
            self.is_running = False
            self._stop_event.set()
            self.log_activity("SYSTEM", "⏸️ Autonomous Autopilot Paused by operator.")
            return True

    def execute_autonomous_cycle(self) -> Dict[str, Any]:
        """Execute one complete hands-free prospecting, emailing, and excel generation cycle."""
        # Pick next region and niche from rotation
        region = US_REGIONS[self.current_region_index % len(US_REGIONS)]
        niche = TARGET_NICHES[self.current_niche_index % len(TARGET_NICHES)]
        self.current_region_index += 1
        self.current_niche_index += 1

        self.log_activity("SCOUT", f"Hunting prospects in {region} for niche: '{niche}'...")

        cycle_summary = {
            "region": region,
            "niche": niche,
            "leads_found": 0,
            "leads_new": 0,
            "emails_dispatched": 0,
            "excel_updated": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with get_db_session() as session:
                # 1. SCOUT: Autonomous Multi-Channel Regional Lead Discovery
                job = self.agency_engine.hunt_regional_agency_leads(
                    location=region,
                    niche=niche,
                    opportunity_type="web_redesign",
                    session=session,
                    max_results=15,
                )
                cycle_summary["leads_found"] = job.leads_found
                cycle_summary["leads_new"] = job.leads_new
                self.total_leads_scouted += job.leads_found

                self.log_activity(
                    "SCOUT",
                    f"Discovered {job.leads_found} businesses in {region} ({job.leads_new} brand new entries added)."
                )

                # 2. EXCEL: Generate Daily Master Spreadsheet (.xlsx)
                excel_path = self.excel_gen.generate_daily_master_sheet(session)
                self.latest_excel_path = str(excel_path)
                cycle_summary["excel_updated"] = True
                self.log_activity("EXPORT", f"Updated Daily Master Excel Sheet: {excel_path.name}")

                # 3. OUTREACH: Autonomous Cold Email Pitching
                if self.auto_email:
                    self.log_activity("EMAIL", f"Auto-pitching uncontacted leads (Mode: {'Dry Run' if self.dry_run else 'Live SMTP'})...")
                    mail_res = self.emailer.run_auto_outreach_campaign(
                        session=session,
                        max_emails=8,
                        dry_run=self.dry_run,
                    )
                    sent = mail_res.get("sent", 0)
                    cycle_summary["emails_dispatched"] = sent
                    self.total_emails_sent += sent
                    self.log_activity("EMAIL", f"Dispatched {sent} tailored agency pitches to verified decision-makers.")

                # 4. REPORT: Dispatch Executive Briefing
                stats = LeadRepository.get_stats(session)
                report_text = (
                    f"Autonomous Cycle #{self.cycles_completed + 1} completed.\n"
                    f"Target: {niche} in {region}.\n"
                    f"New Leads: +{job.leads_new} | Total DB: {stats.get('total_leads', 0)} | Emails Sent: {cycle_summary['emails_dispatched']}."
                )
                self.notifier.broadcast_report("24/7 Agency Autopilot Report", report_text, stats)

            self.cycles_completed += 1
            self.last_cycle_at = datetime.now(timezone.utc)
        except Exception as e:
            self.log_activity("SYSTEM", f"⚠️ Cycle warning: {e}")

        return cycle_summary

    def _autopilot_loop(self) -> None:
        """Continuous background thread."""
        while not self._stop_event.is_set():
            if self.is_running:
                self.execute_autonomous_cycle()
            self._stop_event.wait(timeout=self.interval_seconds)

    def get_mission_control_state(self, session: Session) -> Dict[str, Any]:
        """Return executive metrics, system status, and live activity stream."""
        stats = LeadRepository.get_stats(session)
        leads, _ = LeadRepository.get_leads(session, skip=0, limit=15)

        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "auto_email": self.auto_email,
            "dry_run": self.dry_run,
            "cycles_completed": self.cycles_completed,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "latest_excel_path": self.latest_excel_path,
            "stats": {
                "total_leads": stats.get("total_leads", 0),
                "verified_emails": stats.get("leads_with_email", 0),
                "total_contacted": stats.get("leads_contacted", 0),
                "pending_queue": stats.get("pending_drafts", 0),
                "total_cycles": self.cycles_completed,
            },
            "activity_feed": list(self.activity_logs),
            "recent_leads": [l.to_dict() for l in leads],
            "regions_covered": US_REGIONS,
            "niches_covered": TARGET_NICHES,
        }
