"""Deterministic Technology Detection Engine."""

from __future__ import annotations
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from src.fingerprint.signature_loader import registry, TechSignature


class DetectionResult:
    """Represents a technology detection with provenance evidence."""

    def __init__(
        self,
        tech_id: str,
        name: str,
        category: str,
        confidence: float,
        evidence: List[str],
        status: str,
        version: Optional[str] = None,
    ):
        self.tech_id = tech_id
        self.name = name
        self.category = category
        self.confidence = round(min(confidence, 1.0), 2)
        self.evidence = evidence
        self.status = status  # 'CONFIRMED' or 'POSSIBLE'
        self.version = version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tech_id": self.tech_id,
            "name": self.name,
            "category": self.category,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "status": self.status,
            "version": self.version,
        }


class FingerprintEngine:
    """Scans HTTP responses, HTML DOM, headers, and cookies to identify technologies."""

    @classmethod
    def detect(
        cls,
        html: str = "",
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        target_tech_id: Optional[str] = None,
    ) -> List[DetectionResult]:
        headers = headers or {}
        cookies = cookies or {}
        results: List[DetectionResult] = []

        signatures = [registry.get(target_tech_id)] if target_tech_id and registry.get(target_tech_id) else registry.all()

        soup = None
        if html and ("<html" in html.lower() or "<meta" in html.lower() or "<script" in html.lower()):
            try:
                soup = BeautifulSoup(html[:500000], "html.parser")
            except Exception:
                soup = None

        for sig in signatures:
            if not sig:
                continue

            accumulated_confidence = 0.0
            evidence_list: List[str] = []

            # 1. Check HTML substring / regex patterns
            html_patterns = sig.patterns.get("html", [])
            for p in html_patterns:
                pat = p.get("pattern", "")
                if pat and (pat in html or re.search(pat, html)):
                    weight = float(p.get("weight", 0.3))
                    accumulated_confidence += weight
                    evidence_list.append(p.get("evidence", f"Matched HTML pattern '{pat}'"))

            # 2. Check Meta tags
            if soup:
                meta_patterns = sig.patterns.get("meta", [])
                for p in meta_patterns:
                    name_attr = p.get("name", "").lower()
                    pattern = p.get("pattern", "")
                    if name_attr and pattern:
                        for meta in soup.find_all("meta"):
                            if meta.get("name", "").lower() == name_attr or meta.get("property", "").lower() == name_attr:
                                content = meta.get("content", "")
                                if re.search(pattern, content, re.IGNORECASE):
                                    weight = float(p.get("weight", 0.4))
                                    accumulated_confidence += weight
                                    evidence_list.append(p.get("evidence", f"Meta {name_attr} matched '{content}'"))

            # 3. Check Headers
            header_patterns = sig.patterns.get("headers", [])
            for p in header_patterns:
                header_name = p.get("name", "").lower()
                pattern = p.get("pattern", "")
                for h_key, h_val in headers.items():
                    if h_key.lower() == header_name:
                        if not pattern or re.search(pattern, h_val, re.IGNORECASE):
                            weight = float(p.get("weight", 0.4))
                            accumulated_confidence += weight
                            evidence_list.append(p.get("evidence", f"Header '{h_key}: {h_val}' matched"))

            # 4. Check Cookies
            cookie_patterns = sig.patterns.get("cookies", [])
            for p in cookie_patterns:
                pattern = p.get("pattern", "")
                for c_name, c_val in cookies.items():
                    if re.search(pattern, c_name) or re.search(pattern, f"{c_name}={c_val}"):
                        weight = float(p.get("weight", 0.4))
                        accumulated_confidence += weight
                        evidence_list.append(p.get("evidence", f"Cookie matched '{c_name}'"))

            # 5. Check Script Tags
            if soup:
                script_patterns = sig.patterns.get("scripts", [])
                for p in script_patterns:
                    pattern = p.get("pattern", "")
                    for script in soup.find_all("script"):
                        src = script.get("src", "")
                        if src and re.search(pattern, src):
                            weight = float(p.get("weight", 0.4))
                            accumulated_confidence += weight
                            evidence_list.append(p.get("evidence", f"Script src matched '{src}'"))

            # Only record if some evidence was matched
            if accumulated_confidence > 0.15:
                status = "CONFIRMED" if accumulated_confidence >= sig.confidence_threshold else "POSSIBLE"
                results.append(
                    DetectionResult(
                        tech_id=sig.id,
                        name=sig.name,
                        category=sig.category,
                        confidence=accumulated_confidence,
                        evidence=evidence_list,
                        status=status,
                    )
                )

        results.sort(key=lambda x: x.confidence, reverse=True)
        return results
