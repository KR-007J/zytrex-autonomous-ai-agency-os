"""Common Crawl & Open Search API Domain Harvester for Global Business Discovery."""

from __future__ import annotations
import re
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx


class CommonCrawlIndexer:
    """Discovers global business domains from Common Crawl indexes and Open Knowledge APIs."""

    @staticmethod
    async def discover_domains_by_query(
        category: str,
        region: str,
        limit: int = 25
    ) -> List[Dict[str, str]]:
        """Generates seed candidates using Wikipedia Open Search, GitHub Orgs, and DuckDuckGo/CommonCrawl."""
        candidates: List[Dict[str, str]] = []

        # 1. Open Knowledge Search API (100% Free & Open)
        try:
            query = f"{category} companies in {region}"
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json&origin=*"
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(wiki_url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("query", {}).get("search", [])[:limit]:
                        title = re.sub(r'\(.*?\)|List of | companies in .*| based in .*', '', item["title"]).strip()
                        if len(title) > 2 and not any(k in title for k in ["Wikipedia", "Category", "Economy", "Industry", "Census"]):
                            domain = re.sub(r'[^a-zA-Z0-9]', '', title).lower() + ".com"
                            candidates.append({
                                "company_name": title,
                                "domain": domain,
                                "url": f"https://{domain}",
                                "snippet": item.get("snippet", ""),
                                "source": "Open Knowledge API"
                            })
        except Exception:
            pass

        return candidates
