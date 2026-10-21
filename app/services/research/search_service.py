import os
import re
import httpx
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
        cleaned = re.sub(r"(?i)ignore previous instructions", "[REDACTED_OVERRIDE]", text)
        cleaned = re.sub(r"(?i)system prompt", "[REDACTED_SYSTEM]", cleaned)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        return cleaned.strip()

    async def search(self, query: str, max_results: int = 5) -> SearchResult:
        # Refresh from env so secrets supplied by runtime/deployment after import
        # can be picked up without an application reload.
        self.tavily_key = os.getenv("TAVILY_API_KEY", self.tavily_key).strip()
        if not self.tavily_key:
            return SearchResult(query=query, citations=[], is_live=False, source="unconfigured")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_key,
                        "query": query,
                        "search_depth": "advanced",
                        "include_answer": False,
                        "max_results": max(1, min(max_results, 10))
                    }
                )
                response.raise_for_status()
                payload = response.json()
            citations = []
            for item in payload.get("results", []):
                title = str(item.get("title") or "Untitled source").strip()
                url = str(item.get("url") or "").strip()
                snippet = self.sanitize_untrusted_text(str(item.get("content") or ""))
                if not url.startswith(("https://", "http://")) or not snippet:
                    continue
                citations.append(SearchCitation(title=title, url=url, snippet=snippet))
            return SearchResult(
                query=query,
                citations=citations,
                is_live=bool(citations),
                source="tavily" if citations else "empty_results"
            )
        except Exception as exc:
            # Never label failed/empty results as live.
            return SearchResult(
                query=query, citations=[], is_live=False,
                source=f"error:{type(exc).__name__}"
            )


search_service = SearchService()
