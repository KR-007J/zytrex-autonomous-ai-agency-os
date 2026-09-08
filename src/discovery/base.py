"""Abstract base class for all pluggable Discovery Providers."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional


class CandidateDomain:
    def __init__(
        self,
        domain: str,
        source: str,
        technology_hint: Optional[str] = None,
        country_hint: Optional[str] = None,
        industry_hint: Optional[str] = None,
        confidence_hint: float = 0.5,
    ):
        self.domain = domain.lower().strip()
        self.source = source
        self.technology_hint = technology_hint
        self.country_hint = country_hint
        self.industry_hint = industry_hint
        self.confidence_hint = confidence_hint

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "source": self.source,
            "technology_hint": self.technology_hint,
            "country_hint": self.country_hint,
            "industry_hint": self.industry_hint,
            "confidence_hint": self.confidence_hint,
        }


class DiscoveryProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def discover(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
    ) -> List[CandidateDomain]:
        """Discover candidate domains synchronously or batch."""
        pass

    @abstractmethod
    async def stream(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
        exclude_domains: Optional[set] = None,
    ) -> AsyncGenerator[CandidateDomain, None]:
        """Stream discovered candidate domains asynchronously."""
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Health check for provider."""
        pass
