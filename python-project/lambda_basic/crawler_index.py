"""Crawler that collects all article URLs from shacho.osakazine.net album pages."""

import json
import os
import re
from datetime import datetime

import boto3
import requests
from bs4 import BeautifulSoup

from utils import log_utils

BASE_URL = "https://shacho.osakazine.net"
START_URL = f"{BASE_URL}/album.html"

# Lambda writable directory
OUTPUT_FILE = "/tmp/article_urls.json"

# S3 config
S3_BUCKET = os.environ.get("S3_BUCKET", "vm-ceo-crawler")
S3_KEY = os.environ.get(
    "S3_KEY",
    "crawler/article_urls.json",
)

s3 = boto3.client("s3")


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

DATE_PATTERN = re.compile(r"(\d{4}/\d{2}/\d{2})")


def load_records(output_file: str) -> list[dict]:
    if not os.path.exists(output_file):
        return []

    with open(output_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_records(output_file: str, records: list[dict]) -> None:
    directory = os.path.dirname(output_file)

    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            records,
            f,
            ensure_ascii=False,
            indent=2,
        )


def upload_to_s3(file_path: str):
    """Upload local file to S3."""

    s3.upload_file(
        Filename=file_path,
        Bucket=S3_BUCKET,
        Key=S3_KEY,
    )

    log_utils.crawler(f"Uploaded s3://{S3_BUCKET}/{S3_KEY}")


def crawl_index(output_file: str = OUTPUT_FILE) -> list[str]:
    """Collect all article URLs from album pages and upload result to S3."""

    log_utils.crawler("crawl_index: starting")

    existing_records = load_records(output_file)

    existing_urls = {record["url"] for record in existing_records}

    session = requests.Session()

    session.headers.update({"User-Agent": USER_AGENT})

    url = START_URL
    new_count = 0

    while url:
        log_utils.crawler(f"Crawling: {url}")

        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            log_utils.error(f"Failed to fetch {url}: {e}")
            break

        soup = BeautifulSoup(response.text, "lxml")

        has_new_on_page = False

        for frame in soup.select("div.album div.album_frame"):
            a_tag = frame.select_one("div.album_image a")
            if not a_tag:
                continue

            href = a_tag.get("href", "")
            if not href:
                continue

            article_url = href if href.startswith("http") else f"{BASE_URL}/{href}"

            if article_url in existing_urls:
                continue

            has_new_on_page = True

            title = a_tag.get("title", "")
            date_str = ""
            match = DATE_PATTERN.search(title)
            if match:
                try:
                    date_str = datetime.strptime(match.group(1), "%Y/%m/%d").strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    pass

            existing_records.append(
                {
                    "url": article_url,
                    "date": date_str,
                    "status": "not_crawled",
                    "wp_post_id": None,
                    "wp_post_slug": None,
                }
            )

            existing_urls.add(article_url)
            new_count += 1

        if not has_new_on_page and len(existing_urls) > 0:
            log_utils.crawler("Reached already crawled articles. Stopping pagination.")
            break

        next_url = None
        for a in soup.select("div.page_nav a"):
            if "次へ" in a.get_text(strip=True):
                href = a.get("href", "")
                if href:
                    next_url = href if href.startswith("http") else f"{BASE_URL}/{href}"
                break

        url = next_url

    existing_records.sort(
        key=lambda r: r["date"],
        reverse=True,
    )

    # Save local Lambda file
    save_records(
        output_file,
        existing_records,
    )

    # Upload to S3
    upload_to_s3(output_file)

    log_utils.crawler(
        f"crawl_index: {new_count} new URL(s), {len(existing_records)} total."
    )

    return [record["url"] for record in existing_records]


# if __name__ == "__main__":
#     crawl_index()
