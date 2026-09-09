from __future__ import annotations

import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from urllib.parse import quote_plus, urlparse
from zoneinfo import ZoneInfo

import requests


@dataclass
class NewsItem:
    title: str
    url: str
    seendate: str = ""
    domain: str = ""
    provider: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class NewsFetchStatus:
    fetch_ok: bool
    source: str
    fetched_at: str
    article_count: int
    error: str = ""
    details: str = ""

    def to_dict(self):
        return asdict(self)


class NewsTool:
    """Multi-source news connector.

    GDELT has been removed. The connector now aggregates:
      1) Google News RSS search (no API key required), and
      2) NewsAPI /v2/everything when NEWSAPI_KEY is configured.

    A fetch is considered healthy if at least one provider responds successfully.
    Results are merged and deduplicated so one provider is not a single point of failure.
    """

    NEWSAPI_URL = "https://newsapi.org/v2/everything"
    GOOGLE_RSS_URL = "https://news.google.com/rss/search"

    def __init__(self, timeout=20, retries=3):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Coal-Agentic-OR/6.0 (+academic decision-support prototype)"
        })

    @staticmethod
    def _query() -> str:
        return (
            '(coal OR railway OR rail OR rake OR wagon) AND '
            '(Odisha OR Chhattisgarh OR Talcher OR Korba OR Raigarh) AND '
            '(flood OR rainfall OR monsoon OR waterlogging OR derailment OR '
            '"rake shortage" OR disruption OR strike OR accident)'
        )

    def _request(self, url, *, params=None, headers=None):
        errors = []
        for attempt in range(self.retries):
            try:
                r = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
                if r.status_code == 429:
                    retry_after = r.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                    errors.append(f"429 Too Many Requests (attempt {attempt + 1})")
                    if attempt < self.retries - 1:
                        time.sleep(delay)
                        continue
                r.raise_for_status()
                return r, ""
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
                if attempt < self.retries - 1:
                    time.sleep(2 ** attempt)
        return None, " | ".join(errors)

    def _fetch_newsapi(self, max_records: int) -> Tuple[List[NewsItem], bool, str]:
        api_key = os.getenv("NEWSAPI_KEY", "").strip()
        if not api_key:
            return [], False, "NEWSAPI_KEY not configured"

        now_utc = datetime.now(timezone.utc)
        params = {
            "q": self._query(),
            "from": (now_utc - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"),
            "to": now_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(max_records, 100),
            "page": 1,
        }
        r, error = self._request(
            self.NEWSAPI_URL,
            params=params,
            headers={"X-Api-Key": api_key},
        )
        if r is None:
            return [], False, error

        try:
            raw = r.json()
        except Exception as exc:
            return [], False, f"JSONDecodeError: {exc}"

        if raw.get("status") != "ok":
            return [], False, f"NewsAPI error: {raw.get('code', '')} {raw.get('message', '')}".strip()

        items = []
        for a in raw.get("articles", []):
            url = a.get("url", "") or ""
            source = (a.get("source") or {}).get("name", "") or ""
            items.append(
                NewsItem(
                    title=a.get("title", "") or "",
                    url=url,
                    seendate=a.get("publishedAt", "") or "",
                    domain=source or urlparse(url).netloc,
                    provider="NewsAPI",
                )
            )
        return items, True, ""

    def _fetch_google_rss(self, max_records: int) -> Tuple[List[NewsItem], bool, str]:
        # Google News RSS search is intentionally used as the no-key resilience layer.
        params = {
            "q": self._query(),
            "hl": "en-IN",
            "gl": "IN",
            "ceid": "IN:en",
        }
        r, error = self._request(self.GOOGLE_RSS_URL, params=params)
        if r is None:
            return [], False, error

        try:
            root = ET.fromstring(r.content)
        except Exception as exc:
            return [], False, f"XMLParseError: {exc}"

        items = []
        for node in root.findall("./channel/item")[:max_records]:
            title = (node.findtext("title") or "").strip()
            url = (node.findtext("link") or "").strip()
            pub = (node.findtext("pubDate") or "").strip()
            source_node = node.find("source")
            source = (source_node.text or "").strip() if source_node is not None and source_node.text else ""
            items.append(
                NewsItem(
                    title=title,
                    url=url,
                    seendate=pub,
                    domain=source or urlparse(url).netloc,
                    provider="Google News RSS",
                )
            )
        return items, True, ""

    @staticmethod
    def _dedupe(items: List[NewsItem], max_records: int) -> List[NewsItem]:
        seen = set()
        result = []
        for item in items:
            key = (item.title.strip().lower(), item.url.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
            if len(result) >= max_records:
                break
        return result

    def fetch_with_status(self, max_records=50) -> Tuple[List[NewsItem], NewsFetchStatus]:
        now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()

        rss_items, rss_ok, rss_error = self._fetch_google_rss(max_records)
        api_items, api_ok, api_error = self._fetch_newsapi(max_records)

        items = self._dedupe(rss_items + api_items, max_records)
        healthy = rss_ok or api_ok
        working = []
        if rss_ok:
            working.append("Google News RSS")
        if api_ok:
            working.append("NewsAPI")

        notes = []
        if not rss_ok:
            notes.append(f"Google News RSS failed: {rss_error}")
        if not api_ok:
            notes.append(f"NewsAPI unavailable: {api_error}")

        source = " + ".join(working) if working else "Google News RSS + NewsAPI"
        return items, NewsFetchStatus(
            fetch_ok=healthy,
            source=source,
            fetched_at=now,
            article_count=len(items),
            error="" if healthy else " ; ".join(notes),
            details=" ; ".join(notes) if notes else "Both configured news providers connected",
        )

    def fetch(self, max_records=50) -> List[NewsItem]:
        return self.fetch_with_status(max_records=max_records)[0]
