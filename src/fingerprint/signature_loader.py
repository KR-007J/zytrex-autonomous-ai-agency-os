"""Load and validate technology signature definitions."""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import yaml
from pydantic import BaseModel, Field
from src.config import settings


class PatternRule(BaseModel):
    pattern: str
    weight: float = 0.3
    evidence: str = "Pattern matched"
    name: str | None = None


class TechSignature(BaseModel):
    id: str
    name: str
    category: str
    description: str = ""
    website: str = ""
    confidence_threshold: float = 0.70
    patterns: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)


class SignatureRegistry:
    """In-memory registry of technology signatures."""

    def __init__(self, signatures_dir: Path | None = None):
        self.signatures_dir = signatures_dir or settings.signatures_dir
        self.signatures: Dict[str, TechSignature] = {}
        self.load_signatures()

    def load_signatures(self) -> None:
        self.signatures.clear()
        if not self.signatures_dir.exists():
            return

        for filepath in self.signatures_dir.glob("*.yaml"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "id" in data and "name" in data:
                        sig = TechSignature(**data)
                        self.signatures[sig.id] = sig
            except Exception as e:
                print(f"Warning: Failed to load signature {filepath}: {e}")

    def get(self, tech_id: str) -> TechSignature | None:
        return self.signatures.get(tech_id)

    def all(self) -> List[TechSignature]:
        return list(self.signatures.values())


registry = SignatureRegistry()
