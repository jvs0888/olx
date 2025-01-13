import asyncio
from src.olx_scraper import OlxScraper


def run() -> None:
    olx: OlxScraper = OlxScraper()
    asyncio.run(olx.run())


if __name__ == '__main__':
    run()
