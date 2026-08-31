"""Notification dispatcher for Telegram, Slack, Email, and Hermes Gateway."""

from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
import httpx
import logging

from src.config import RootConfig, load_config

logger = logging.getLogger("leadgen.notifier")


class NotificationDispatcher:
    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()
        self.client = httpx.Client(timeout=10.0)

    def send_telegram(self, message: str) -> bool:
        """Send message via Telegram Bot API."""
        tg = self.config.notifications.telegram
        if not tg.enabled or not tg.bot_token or not tg.chat_id:
            return False

        url = f"https://api.telegram.org/bot{tg.bot_token}/sendMessage"
        payload = {"chat_id": tg.chat_id, "text": message, "parse_mode": "HTML"}

        try:
            resp = self.client.post(url, json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram notification error: {e}")
            return False

    def send_slack(self, message: str) -> bool:
        """Send message via Slack Webhook."""
        sl = self.config.notifications.slack
        if not sl.enabled or not sl.webhook_url:
            return False

        payload = {"text": message}
        try:
            resp = self.client.post(sl.webhook_url, json=payload)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return False

    def send_email(self, subject: str, body: str) -> bool:
        """Send email via SMTP."""
        em = self.config.notifications.email
        if not em.enabled or not em.recipient or not em.smtp_user:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = em.smtp_user
            msg["To"] = em.recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(em.smtp_host, em.smtp_port) as server:
                server.starttls()
                if em.smtp_pass:
                    server.login(em.smtp_user, em.smtp_pass)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Email notification error: {e}")
            return False

    def broadcast_report(self, title: str, summary: str, stats: Dict[str, Any]) -> Dict[str, bool]:
        """Broadcast summary report across all enabled channels."""
        formatted_text = f"📊 <b>{title}</b>\n\n{summary}\n\n"
        formatted_text += f"• <b>Total Leads:</b> {stats.get('total_leads', 0)}\n"
        formatted_text += f"• <b>With Email:</b> {stats.get('leads_with_email', 0)}\n"
        formatted_text += f"• <b>With Phone:</b> {stats.get('leads_with_phone', 0)}\n"
        formatted_text += f"• <b>Contacted:</b> {stats.get('leads_contacted', 0)}\n"
        formatted_text += f"• <b>Pending Queue:</b> {stats.get('pending_drafts', 0)}\n"

        results = {
            "telegram": self.send_telegram(formatted_text),
            "slack": self.send_slack(formatted_text.replace("<b>", "*").replace("</b>", "*")),
            "email": self.send_email(title, formatted_text.replace("<b>", "").replace("</b>", "")),
        }
        return results
