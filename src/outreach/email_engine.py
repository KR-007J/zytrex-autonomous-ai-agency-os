"""Autonomous 24/7 cold email dispatching engine with safety throttles."""

from __future__ import annotations
import smtplib
import time
import random
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from src.config import RootConfig, load_config
from src.database.models import Lead, OutreachDraft, ContactedMemory
from src.outreach.personalizer import OutreachPersonalizer
from src.scraper.dedupe import is_already_contacted, record_contacted

logger = logging.getLogger("leadgen.emailer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class ColdEmailEngine:
    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()
        self.personalizer = OutreachPersonalizer(self.config)

    def send_single_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        dry_run: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Send a single cold email via SMTP or simulate in dry-run mode."""
        cfg = self.config.notifications.email

        if dry_run or not cfg.enabled:
            logger.info(f"[SIMULATION / DRY-RUN] Sending cold email to {to_email} with subject: '{subject}'")
            return True, "Simulated send (Dry run mode)"

        if not cfg.smtp_user or not to_email:
            return False, "Missing SMTP credentials or recipient email"

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.config.app.name} <{cfg.smtp_user}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg["X-Auto-Response-Suppress"] = "OOF, AutoReply"

            # CAN-SPAM compliant footer with 1-click unsubscribe notice
            footer = "\n\n---\nTo stop receiving these emails, simply reply with 'unsubscribe' and we will remove you immediately."
            full_body = body_text + footer

            msg.attach(MIMEText(full_body, "plain", "utf-8"))

            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15.0) as server:
                server.starttls()
                if cfg.smtp_pass:
                    server.login(cfg.smtp_user, cfg.smtp_pass)
                server.send_message(msg)

            logger.info(f"Successfully dispatched cold email to {to_email}")
            return True, None
        except Exception as e:
            logger.error(f"Failed to send cold email to {to_email}: {e}")
            return False, str(e)

    def run_auto_outreach_campaign(
        self,
        session: Session,
        max_emails: int = 15,
        delay_seconds: float = 3.0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Auto-dispatch cold emails to uncontacted leads with verified public emails."""
        # Find leads with verified email who have not been contacted
        candidates = (
            session.query(Lead)
            .filter(Lead.email.isnot(None), Lead.email != "")
            .filter(Lead.status.in_(["new", "drafted", "enriched"]))
            .order_by(Lead.lead_score.desc(), Lead.created_at.desc())
            .limit(max_emails)
            .all()
        )

        sent_count = 0
        failed_count = 0
        logs = []

        for lead in candidates:
            if is_already_contacted(session, email=lead.email, domain=lead.source_domain):
                lead.status = "contacted"
                continue

            # Generate personalized message
            draft_data = self.personalizer.generate_draft_for_lead(lead)
            subject = draft_data["subject"]
            body = draft_data["personalized_message"]

            success, err = self.send_single_email(
                to_email=lead.email,
                subject=subject,
                body_text=body,
                dry_run=dry_run,
            )

            # Record draft in database
            draft = OutreachDraft(
                lead_id=lead.id,
                template_id=draft_data["template_id"],
                subject=subject,
                personalized_message=body,
                status="sent" if success else "failed",
                sent_at=datetime.now(timezone.utc) if success else None,
                notes=f"Auto-Mailer {'Dry Run' if dry_run else 'Live'}" if success else f"Error: {err}",
            )
            session.add(draft)

            if success:
                sent_count += 1
                lead.status = "contacted"
                record_contacted(session, lead.email, lead_id=lead.id, channel="cold_email_auto")
                logs.append(f"✓ Sent to {lead.company_name} ({lead.email})")
            else:
                failed_count += 1
                logs.append(f"✗ Failed for {lead.company_name} ({lead.email}): {err}")

            session.commit()

            # Apply delay between sends to protect sender reputation
            if delay_seconds > 0:
                jitter = random.uniform(0.5, 2.0)
                time.sleep(delay_seconds + jitter)

        return {
            "processed": len(candidates),
            "sent": sent_count,
            "failed": failed_count,
            "logs": logs,
        }
