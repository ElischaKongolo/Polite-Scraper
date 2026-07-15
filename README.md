# Polite Scraper

Polite Scraper is a Python-based web scraping project designed for the Week 4 backend AI engineering assignment. It demonstrates the full pipeline of fetching, parsing, cleaning, and structuring webpage content while following a more responsible, bot-friendly approach.

## What this project does

- Fetches pages from a starting URL
- Extracts page titles and clean body text
- Follows same-domain links
- Respects a simple robots.txt disallow rule when present
- Saves structured records as JSONL or CSV
- Includes a command-line interface for easy use

## Project structure

- polite_scraper.py — core scraper implementation
- cli.py — command-line entry point
- tests/ — test suite and fixture pages
- example.py — simple usage example
- README.md — project overview and instructions

## Setup

1. Clone the repository
2. Install Python 3.10+ if needed
3. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the tests

```bash
python -m pytest -q
```

## Example usage

### Python API

```python
from polite_scraper import PoliteScraper, ScraperConfig

scraper = PoliteScraper(ScraperConfig(start_url="https://example.com", max_pages=3, delay_seconds=0.5))
records = scraper.crawl()
scraper.save_records("output/records.jsonl", format="jsonl")
```

### Command line

```bash
python cli.py https://example.com --max-pages 2 --delay 0 --output output/demo.jsonl
```

## Notes

This project is intentionally designed as a polite and educational scraper. It is suitable for practice sites and learning workflows rather than aggressive crawling.

