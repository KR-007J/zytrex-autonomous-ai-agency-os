"""Personalization engine using Jinja2 templates and contextual enrichment."""

from __future__ import annotations
from typing import Optional, Dict, Any
from jinja2 import Template, Environment, BaseLoader

from src.config import RootConfig, load_config, TemplateConfig
from src.database.models import Lead


class OutreachPersonalizer:
    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()
        self.env = Environment(loader=BaseLoader(), autoescape=False)

    def render_template(
        self,
        template_str: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a template string with fallback dictionary context."""
        try:
            jinja_tpl = self.env.from_string(template_str)
            return jinja_tpl.render(**context).strip()
        except Exception as e:
            # Fallback simple replacement if Jinja fails on syntax
            result = template_str
            for key, val in context.items():
                result = result.replace(f"{{{{ {key} }}}}", str(val or ""))
                result = result.replace(f"{{{{{key}}}}}", str(val or ""))
            return result.strip()

    def generate_draft_for_lead(
        self,
        lead: Lead,
        template_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate subject and personalized body for a given lead."""
        templates = self.config.linkedin.templates
        tid = template_id or self.config.linkedin.manual_assist.default_template_id

        tpl_config = templates.get(tid)
        if not tpl_config:
            # Default fallback template
            tpl_config = TemplateConfig(
                id="default_b2b",
                name="Default B2B Outreach",
                subject="Quick question for {{ contact_name or company_name }}",
                body="Hi {{ contact_name or 'there' }},\n\nI noticed {{ company_name }}'s work in {{ industry_tag or 'your industry' }}.\n\nWould love to connect and share some ideas around scaling outbound pipeline.\n\nBest,\nOutreach Team",
            )

        context = {
            "contact_name": lead.contact_name,
            "company_name": lead.company_name,
            "email": lead.email,
            "phone": lead.phone,
            "source_url": lead.source_url,
            "source_domain": lead.source_domain,
            "industry_tag": lead.industry_tag,
            "location": lead.location,
            "lead_score": lead.lead_score,
        }

        subject = self.render_template(tpl_config.subject, context)
        body = self.render_template(tpl_config.body, context)

        return {
            "template_id": tpl_config.id,
            "template_name": tpl_config.name,
            "subject": subject,
            "personalized_message": body,
        }
