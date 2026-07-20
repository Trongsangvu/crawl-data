"""Scrapy crawler that collects all article URLs from shacho.osakazine.net album pages."""

import json
import logging
import os
import re
from datetime import datetime

import scrapy
from scrapy.crawler import CrawlerProcess
from utils import log_utils

logging.getLogger("scrapy").setLevel(logging.WARNING)
logging.getLogger("scrapy").propagate = False

BASE_URL = "https://shacho.osakazine.net"
START_URL = f"{BASE_URL}/album.html"
OUTPUT_FILE = "data/article_urls.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DATE_PATTERN = re.compile(r"(\d{4}/\d{2}/\d{2})")


class AlbumSpider(scrapy.Spider):
    """Spider that walks album pages collecting article URLs."""

    name = "album"
    handle_httpstatus_list = [404]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.articles: list[dict] = []

    async def start(self):
        log_utils.crawler(f"album spider starting from {START_URL}")
        yield scrapy.Request(url=START_URL, callback=self.parse)

    def parse(self, response):
        """Parse the album page, collect article URLs, and follow to the next page."""
        if response.status == 404:
            log_utils.crawler("404 — stopping")
            return

        count_before = len(self.articles)
        for frame in response.css("div.album div.album_frame"):
            a_tag = frame.css("div.album_image a")
            if not a_tag:
                continue
            href = a_tag.attrib.get("href", "")
            if not href:
                continue
            title = a_tag.attrib.get("title", "")
            m = DATE_PATTERN.search(title)
            date_str = ""
            if m:
                try:
                    date_str = datetime.strptime(m.group(1), "%Y/%m/%d").strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    pass
            url = href if href.startswith("http") else f"{BASE_URL}/{href}"
            self.articles.append({"url": url, "date": date_str})

        found = len(self.articles) - count_before
        log_utils.crawler(
            f"{response.url}: {found} article(s) found (total {len(self.articles)})"
        )

        next_href = None
        for a in response.css("div.page_nav a"):
            if "次へ" in (a.css("::text").get("") or ""):
                next_href = a.attrib.get("href", "")
                break

        if next_href:
            log_utils.crawler(f"following next page: {next_href}")
            yield response.follow(next_href, callback=self.parse)
        else:
            log_utils.crawler("no next page — done")


def crawl_index(output_file: str = OUTPUT_FILE) -> list[str]:
    """Run the album spider and save collected article URLs to output_file."""
    log_utils.crawler(f"crawl_index: starting, output → {output_file}")
    process = CrawlerProcess(
        {
            "USER_AGENT": USER_AGENT,
            "DOWNLOAD_DELAY": 1,
            "ROBOTSTXT_OBEY": False,
        }
    )
    crawler = process.create_crawler(AlbumSpider)
    process.crawl(crawler)
    process.start()

    spider: AlbumSpider = crawler.spider  # type: ignore
    articles = spider.articles if spider else []

    records = sorted(
        [
            {
                "url": a["url"],
                "date": a["date"],
                "status": "not_crawled",
                "wp_post_id": None,
                "wp_post_slug": None,
            }
            for a in articles
        ],
        key=lambda r: r["date"],
        reverse=False,
    )
    if os.environ.get("AWS_EXECUTION_ENV"):
        output_file = "/tmp/article_urls.json"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    log_utils.crawler(
        f"crawl_index: done — saved {len(articles)} URLs to {output_file}"
    )
    return [a["url"] for a in articles]


if __name__ == "__main__":
    crawl_index()
