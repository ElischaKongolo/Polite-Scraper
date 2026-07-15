from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen, url2pathname


@dataclass
class ScraperConfig:
    start_url: str
    max_pages: int = 10
    delay_seconds: float = 0.0
    user_agent: str = "FlyRankAI-PoliteScraper/1.0 (+https://example.com/bot)"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "noscript"}

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_name = tag.lower()
        if tag_name in self._skip_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in self._skip_tags and self._skip_depth:
            self._skip_depth -= 1


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "a":
            return
        for attr_name, attr_value in attrs:
            if attr_name.lower() == "href" and attr_value:
                self.links.append(attr_value)


class PoliteScraper:
    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self.visited: set[str] = set()
        self.records: List[Dict[str, str]] = []
        self._robots_rules: Dict[str, List[Tuple[str, str]]] = {}
        self._queue: List[str] = []

    def crawl(self) -> List[Dict[str, str]]:
        self._queue = [self.config.start_url]
        while self._queue:
            url = self._queue.pop(0)
            if url in self.visited:
                continue
            if len(self.records) >= self.config.max_pages:
                break
            if not self._is_allowed(url):
                self.visited.add(url)
                continue

            response_text = self._fetch(url)
            if response_text is None:
                self.visited.add(url)
                continue

            self.visited.add(url)
            record = self._parse_record(url, response_text)
            if record:
                self.records.append(record)

            for link in self._extract_links(response_text, url):
                if link not in self.visited and link not in self._queue:
                    self._queue.append(link)

            if self.config.delay_seconds:
                time.sleep(self.config.delay_seconds)

        return self.records

    def _fetch(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            path = Path(url2pathname(parsed.path))
            if not path.exists():
                return None
            return path.read_text(encoding="utf-8")

        request = Request(url, headers={"User-Agent": self.config.user_agent})
        try:
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception:
            return None

    def _parse_record(self, url: str, html: str) -> Optional[Dict[str, str]]:
        parser = _TextExtractor()
        parser.feed(html)
        body_text = self._clean_text(" ".join(parser.parts))
        title = self._extract_title(html)
        if not body_text and not title:
            return None
        return {
            "title": title,
            "body_text": body_text,
            "source_url": url,
        }

    def _extract_title(self, html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return self._clean_text(match.group(1))
        return ""

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        parser = _LinkExtractor()
        parser.feed(html)
        links: List[str] = []
        for href in parser.links:
            absolute = urljoin(base_url, href)
            if self._is_same_domain(absolute, base_url):
                links.append(absolute)
        return links

    def _is_same_domain(self, url: str, base_url: str) -> bool:
        return urlparse(url).netloc == urlparse(base_url).netloc

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path or "/"
        robots_url = self._robots_url_for(parsed)
        rules = self._robots_rules.get(robots_url)
        if rules is None:
            rules = self._load_robots_rules(robots_url)
            self._robots_rules[robots_url] = rules

        for _, pattern in rules:
            if pattern and self._matches_path(pattern, path):
                return False
        return True

    def _matches_path(self, pattern: str, path: str) -> bool:
        if not pattern:
            return False
        if pattern.startswith("/"):
            pattern = pattern[1:]
        if pattern.endswith("$"):
            pattern = pattern[:-1]
        return path.rstrip("/") == f"/{pattern}" or path.rstrip("/").endswith(f"/{pattern}")

    def _robots_url_for(self, parsed) -> str:
        if parsed.scheme == "file":
            path = Path(url2pathname(parsed.path))
            return str(path.parent / "robots.txt")
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _load_robots_rules(self, robots_url: str) -> List[Tuple[str, str]]:
        path_candidate = None
        if robots_url.startswith("file://"):
            path_candidate = Path(url2pathname(urlparse(robots_url).path))
        elif robots_url.startswith("http://") or robots_url.startswith("https://"):
            request = Request(robots_url, headers={"User-Agent": self.config.user_agent})
            try:
                with urlopen(request, timeout=10) as response:
                    text = response.read().decode("utf-8", errors="ignore")
            except Exception:
                return []
        else:
            path_candidate = Path(robots_url)

        if path_candidate is not None:
            if not path_candidate.exists():
                return []
            text = path_candidate.read_text(encoding="utf-8")
        else:
            return []

        rules: List[Tuple[str, str]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.lower().startswith("disallow:"):
                path = stripped.split(":", 1)[1].strip()
                if path:
                    rules.append(("disallow", path))
        return rules

    def save_records(self, output_path: str | Path, format: str = "jsonl") -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "jsonl":
            with path.open("w", encoding="utf-8") as handle:
                for record in self.records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        elif format.lower() == "csv":
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["title", "body_text", "source_url"])
                writer.writeheader()
                writer.writerows(self.records)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return path

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()
