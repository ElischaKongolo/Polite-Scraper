import csv
import json
from pathlib import Path

import pytest

from polite_scraper import PoliteScraper, ScraperConfig


@pytest.fixture
def fixture_dir(tmp_path):
    fixture_root = Path(__file__).parent / "fixtures"
    target = tmp_path / "site"
    target.mkdir()
    for path in fixture_root.glob("*"):
        if path.is_file():
            target.joinpath(path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_extracts_and_cleans_page_content(fixture_dir):
    start_url = fixture_dir.joinpath("index.html").as_uri()
    scraper = PoliteScraper(ScraperConfig(start_url=start_url, max_pages=5, delay_seconds=0))

    records = scraper.crawl()

    assert len(records) == 2
    first = records[0]
    assert first["title"] == "Demo Campus"
    assert "Campus guide" in first["body_text"]
    assert "Welcome to Demo Campus" in first["body_text"]
    assert first["source_url"].endswith("index.html")


def test_ignores_pages_disallowed_by_robots_txt(fixture_dir):
    start_url = fixture_dir.joinpath("index.html").as_uri()
    scraper = PoliteScraper(ScraperConfig(start_url=start_url, max_pages=5, delay_seconds=0))

    records = scraper.crawl()

    assert all("private" not in record["source_url"] for record in records)


def test_saves_records_as_jsonl(tmp_path):
    scraper = PoliteScraper(ScraperConfig(start_url="https://example.com", max_pages=1, delay_seconds=0))
    scraper.records = [{"title": "Demo", "body_text": "Hello world", "source_url": "https://example.com"}]

    output_path = tmp_path / "records.jsonl"
    scraper.save_records(output_path, format="jsonl")

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8").strip())
    assert payload["title"] == "Demo"


def test_saves_records_as_csv(tmp_path):
    scraper = PoliteScraper(ScraperConfig(start_url="https://example.com", max_pages=1, delay_seconds=0))
    scraper.records = [{"title": "Demo", "body_text": "Hello world", "source_url": "https://example.com"}]

    output_path = tmp_path / "records.csv"
    scraper.save_records(output_path, format="csv")

    assert output_path.exists()
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["title"] == "Demo"
