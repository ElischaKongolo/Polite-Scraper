import argparse

from polite_scraper import PoliteScraper, ScraperConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape a site politely and save structured records")
    parser.add_argument("url", help="The starting URL to crawl")
    parser.add_argument("--output", default="output/records.jsonl", help="Output file path")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to scrape")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds")
    parser.add_argument("--format", choices=["jsonl", "csv"], default="jsonl", help="Output file format")
    args = parser.parse_args()

    scraper = PoliteScraper(
        ScraperConfig(
            start_url=args.url,
            max_pages=args.max_pages,
            delay_seconds=args.delay,
        )
    )
    scraper.crawl()
    scraper.save_records(args.output, format=args.format)
    print(f"Saved {len(scraper.records)} records to {args.output}")


if __name__ == "__main__":
    main()
