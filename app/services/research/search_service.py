import os
import re
import httpx
from typing import Optional
from pydantic import BaseModel, Field
from app.agents.base import current_time_iso

class SearchCitation(BaseModel):
    title: str
    url: str
    snippet: str
    retrieved_at: str = Field(default_factory=current_time_iso)

class SearchResult(BaseModel):
    query: str
    citations: list[SearchCitation] = Field(default_factory=list)
    is_live: bool = False
    source: str = "none"

class SearchService:
    def __init__(self):
        self.tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.search_key = os.getenv("SEARCH_API_KEY", "").strip()

    def sanitize_untrusted_text(self, text: str) -> str:
        """Sanitizes web search snippets to mitigate prompt injection risks."""
        # Strip potential instruction overrides or tags
        cleaned = re.sub(r"(?i)ignore previous instructions", "[REDACTED_OVERRIDE]", text)
        cleaned = re.sub(r"(?i)system prompt", "[REDACTED_SYSTEM]", cleaned)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        return cleaned.strip()

    async def search(self, query: str, max_results: int = 5) -> SearchResult:
        if not self.tavily_key and not self.search_key:
            return SearchResult(
                query=query,
                citations=[],
                is_live=False,
                source="unconfigured"
            )

        # Tavily Search API
        if self.tavily_key:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": self.tavily_key,
                            "query": query,
                            "search_depth": "basic",
                            "include_answer": False,
                            "max_results": max_results
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        citations = [
                            SearchCitation(
                                title=r.get("title", "Search Result"),
                                url=r.get("url", ""),
                                snippet=self.sanitize_untrusted_text(r.get("content", ""))
                            )
                            for r in data.get("results", [])
                        ]
                        return SearchResult(
                            query=query,
                            citations=citations,
                            is_live=True,
                            source="tavily"
                        )
            except Exception:
                pass

        return SearchResult(query=query, citations=[], is_live=False, source="error_fallback")

search_service = SearchService()
