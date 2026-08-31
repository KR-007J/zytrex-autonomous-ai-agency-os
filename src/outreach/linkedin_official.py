"""Official LinkedIn Marketing Developer Platform Integration (Lead Sync API).

NOTE ON COMPLIANCE & ARCHITECTURAL BOUNDARIES:
- Official LinkedIn API approval is provided exclusively for Marketing Developer Platform
  partners using the 'Lead Sync API' (capturing inbound leads from paid Lead Gen Forms).
- The Sales Navigator API and general outbound DM APIs are strictly restricted / closed
  to third-party prospecting bots.
- Outbound prospecting in this system is therefore routed through the 100% compliant
  Manual-Assist queue (see `src/outreach/manual_assist.py`).
- This module implements the official Lead Sync API for clients who run LinkedIn ad forms.
"""

from __future__ import annotations
import urllib.parse
import httpx
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from src.config import RootConfig, load_config, OfficialApiConfig
from src.database.db import LeadRepository
from src.scraper.dedupe import normalize_lead_dict


class LinkedInOfficialLeadSyncClient:
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_BASE = "https://api.linkedin.com/v2"

    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()
        self.api_cfg: OfficialApiConfig = self.config.linkedin.official_api
        self.client = httpx.Client(timeout=15.0)

    def get_authorization_url(self, state: str = "secure_leadgen_state") -> str:
        """Generate official OAuth 2.0 authorization URL for Lead Sync."""
        params = {
            "response_type": "code",
            "client_id": self.api_cfg.client_id or "CLIENT_ID_PLACEHOLDER",
            "redirect_uri": self.api_cfg.redirect_uri,
            "state": state,
            "scope": "r_ads_leadgen_automation rw_ads r_liteprofile r_emailaddress",
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange OAuth authorization code for access token."""
        if not self.api_cfg.client_id or not self.api_cfg.client_secret:
            raise ValueError("LinkedIn client_id and client_secret must be set in config.yaml")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.api_cfg.redirect_uri,
            "client_id": self.api_cfg.client_id,
            "client_secret": self.api_cfg.client_secret,
        }
        resp = self.client.post(self.TOKEN_URL, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        return token_data

    def fetch_lead_gen_responses(
        self,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch form response submissions from LinkedIn Lead Gen Forms."""
        token = access_token or self.api_cfg.access_token
        account = ad_account_id or self.api_cfg.ad_account_id

        if not token:
            return []

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        url = f"{self.API_BASE}/adFormResponses"
        params = {"q": "account", "account": account} if account else {}

        resp = self.client.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            return []

        data = resp.json()
        return data.get("elements", [])

    def sync_ad_leads_to_db(self, session: Session, access_token: Optional[str] = None) -> int:
        """Sync submitted ad leads into the leads database."""
        responses = self.fetch_lead_gen_responses(access_token)
        synced = 0

        for item in responses:
            form_answers = {ans.get("questionId"): ans.get("value") for ans in item.get("answers", [])}

            raw_lead = {
                "company_name": form_answers.get("companyName") or "LinkedIn Ad Lead",
                "contact_name": f"{form_answers.get('firstName', '')} {form_answers.get('lastName', '')}".strip(),
                "email": form_answers.get("emailAddress"),
                "phone": form_answers.get("phoneNumber"),
                "source_url": "https://www.linkedin.com/ads",
                "industry_tag": form_answers.get("industry") or "Inbound Lead Gen Form",
                "location": form_answers.get("city"),
                "lead_score": 90,  # High intent opt-in
                "status": "new",
                "raw_snippet": "Inbound submission via LinkedIn Lead Gen Form",
            }

            normalized = normalize_lead_dict(raw_lead)
            _, is_new = LeadRepository.create_or_update(session, normalized)
            if is_new:
                synced += 1

        session.commit()
        return synced
