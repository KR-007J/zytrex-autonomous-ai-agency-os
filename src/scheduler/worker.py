"""24/7 Background Autonomous Worker Daemon for continuous scraping, emailing, and Excel reporting."""

from __future__ import annotations
import time
import threading
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from src.config import RootConfig, load_config
from src.database.db import get_db_session, LeadRepository
from src.scraper.engine import ScraperEngine
from src.outreach.email_engine import ColdEmailEngine
from src.export.excel_generator import ExcelReportGenerator
from src.notifications.notifier import NotificationDispatcher

logger = logging.getLogger("leadgen.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class AutonomousLeadWorker:
    _instance: Optional[AutonomousLeadWorker] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AutonomousLeadWorker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config: Optional[RootConfig] = None):
        if getattr(self, "_initialized", False):
            return
        self.config = config or load_config()
        self.scraper = ScraperEngine(self.config)
        self.emailer = ColdEmailEngine(self.config)
        self.excel_gen = ExcelReportGenerator()
        self.notifier = NotificationDispatcher(self.config)

        self.is_running = False
        self.interval_seconds = 3600  # Default: runs every hour (3600s)
        self.auto_email_enabled = False
        self.dry_run = True

        self.last_run_at: Optional[datetime] = None
        self.next_run_at: Optional[datetime] = None
        self.cycles_completed = 0
        self.last_error: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._initialized = True

    def start(self, interval_seconds: int = 3600, auto_email: bool = False, dry_run: bool = True) -> bool:
        """Start the 24/7 autonomous background worker thread."""
        with self._lock:
            if self.is_running:
                return True

            self.interval_seconds = interval_seconds
            self.auto_email_enabled = auto_email
            self.dry_run = dry_run
            self.is_running = True
            self._stop_event.clear()

            self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="LeadGen247Daemon")
            self._thread.start()
            logger.info("⚡ Autonomous 24/7 Lead Worker Daemon started successfully.")
            return True

    def stop(self) -> bool:
        """Stop the background worker thread."""
        with self._lock:
            if not self.is_running:
                return False
            self.is_running = False
            self._stop_event.set()
            logger.info("⏹️ Autonomous 24/7 Lead Worker Daemon stopping...")
            return True

    def trigger_cycle(self) -> Dict[str, Any]:
        """Execute a single end-to-end autonomous cycle immediately."""
        logger.info("🔄 Running Autonomous Prospecting & Reporting Cycle...")
        start_time = datetime.now(timezone.utc)
        result = {
            "started_at": start_time.isoformat(),
            "leads_found": 0,
            "leads_new": 0,
            "emails_sent": 0,
            "excel_path": None,
            "status": "success",
            "error": None,
        }

        try:
            with get_db_session() as session:
                # 1. Scrape Multi-Social and Directory Platforms
                jobs = self.scraper.run_all_configured_scrapers(session)
                result["leads_found"] = sum(j.leads_found for j in jobs)
                result["leads_new"] = sum(j.leads_new for j in jobs)

                # 2. Automated Multi-Tab Excel Spreadsheet Generation
                excel_path = self.excel_gen.generate_daily_master_sheet(session)
                result["excel_path"] = str(excel_path)

                # 3. Autonomous Cold Email Campaign (if enabled)
                if self.auto_email_enabled:
                    mail_res = self.emailer.run_auto_outreach_campaign(
                        session=session,
                        max_emails=10,
                        dry_run=self.dry_run,
                    )
                    result["emails_sent"] = mail_res.get("sent", 0)

                # 4. Broadcast notification summary
                stats = LeadRepository.get_stats(session)
                summary = f"Autonomous Cycle #{self.cycles_completed + 1} completed: Found {result['leads_found']} leads (+{result['leads_new']} new). Excel sheet updated."
                self.notifier.broadcast_report("24/7 Agent Cycle Report", summary, stats)

            self.cycles_completed += 1
            self.last_run_at = datetime.now(timezone.utc)
            self.last_error = None
        except Exception as e:
            logger.error(f"Autonomous cycle encountered an error: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            self.last_error = str(e)

        return result

    def _worker_loop(self) -> None:
        """Continuous background daemon loop."""
        while not self._stop_event.is_set():
            self.trigger_cycle()
            # Wait for next interval or stop signal
            self._stop_event.wait(timeout=self.interval_seconds)

    def get_status(self) -> Dict[str, Any]:
        """Return real-time agent status."""
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "auto_email_enabled": self.auto_email_enabled,
            "dry_run": self.dry_run,
            "cycles_completed": self.cycles_completed,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_error": self.last_error,
        }
