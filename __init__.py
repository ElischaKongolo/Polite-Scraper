try:
    from .polite_scraper import PoliteScraper, ScraperConfig
except ImportError:  # pragma: no cover - allows pytest to collect the root package safely
    from polite_scraper import PoliteScraper, ScraperConfig

__all__ = ["PoliteScraper", "ScraperConfig"]
