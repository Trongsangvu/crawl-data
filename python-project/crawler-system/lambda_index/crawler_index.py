"""Crawler that collects all article URLs from shacho.osakazine.net album pages."""

import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from utils import log_utils

BASE_URL = "https://shacho.osakazine.net"
START_URL = f"{BASE_URL}/album.html"
OUTPUT_FILE = "data/article_urls.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DATE_PATTERN = re.compile(r"(\d{4}/\d{2}/\d{2})")


def crawl_index(output_file: str = OUTPUT_FILE) -> list[str]:
    """Collect all article URLs from album pages."""

    if os.environ.get("AWS_EXECUTION_ENV"):
        output_file = "/tmp/article_urls.json"

    log_utils.crawler(f"crawl_index: starting, output → {output_file}")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    url = START_URL
    articles: list[dict] = []

    while url:
        log_utils.crawler(f"Crawling: {url}")

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            log_utils.error(f"Failed to fetch {url}: {e}")
            break

        soup = BeautifulSoup(response.text, "lxml")

        count_before = len(articles)

        for frame in soup.select("div.album div.album_frame"):
            a_tag = frame.select_one("div.album_image a")

            if not a_tag:
                continue

            href = a_tag.get("href", "")
            if not href:
                continue

            title = a_tag.get("title", "")

            date_str = ""
            m = DATE_PATTERN.search(title)

            if m:
                try:
                    date_str = datetime.strptime(
                        m.group(1),
                        "%Y/%m/%d",
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass

            article_url = href if href.startswith("http") else f"{BASE_URL}/{href}"

            articles.append(
                {
                    "url": article_url,
                    "date": date_str,
                }
            )

        found = len(articles) - count_before

        log_utils.crawler(f"{url}: {found} article(s) found (total {len(articles)})")

        next_url = None

        for a in soup.select("div.page_nav a"):
            if "次へ" in a.get_text(strip=True):
                href = a.get("href", "")
                if href:
                    next_url = href if href.startswith("http") else f"{BASE_URL}/{href}"
                break

        if next_url:
            log_utils.crawler(f"following next page: {next_url}")
        else:
            log_utils.crawler("no next page — done")

        url = next_url

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
    )

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    log_utils.crawler(f"crawl_index: done — saved {len(records)} URLs to {output_file}")

    return [r["url"] for r in records]


if __name__ == "__main__":
    crawl_index()
