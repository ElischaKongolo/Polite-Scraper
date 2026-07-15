from polite_scraper import PoliteScraper, ScraperConfig

scraper = PoliteScraper(ScraperConfig(start_url="https://example.com", max_pages=3, delay_seconds=0.5))
records = scraper.crawl()
print(records[:1])
