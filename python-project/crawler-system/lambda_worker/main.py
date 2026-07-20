"""Main entry point for the sacho-osaka crawler."""

import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup, Comment, NavigableString
# from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import log_utils
from integrations.app_client import save_ceo_interview

sys.path.insert(0, os.path.dirname(__file__))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def parse_date_to_timestamp(date_str: str) -> int | None:
    """Parse a date string to a UTC Unix timestamp (seconds).

    Handles ISO format (2026-04-10, 2026-04-10T00:31:07+09:00)
    and Japanese format (2026年04月10日).
    """
    if not date_str:
        return None
    # Collapse whitespace/CRLF (e.g. "2023-03-24\r\n            09:30" → "2023-03-24 09:30")
    date_str = re.sub(r"[\r\n]+\s*", " ", date_str).strip()
    # Normalise Japanese format → ISO
    date_str = re.sub(r"(\d{4})年(\d{1,2})月(\d{1,2})日", r"\1-\2-\3", date_str)
    formats = ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[: len(fmt) + 6], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.astimezone(timezone.utc).timestamp())
        except ValueError:
            continue
    log_utils.warning(f"Could not parse date: {date_str!r}")
    return None


def crawl_article(url: str) -> dict | None:
    """Fetch a single article page and return parsed title + content HTML."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        log_utils.error(f"Request failed for {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("h3", class_="title", itemprop="headline")
    title = title_tag.get_text(strip=True) if title_tag else ""

    content_tag = soup.find("div", class_="main-post", itemprop="articleBody")
    content_html = str(content_tag) if content_tag else ""

    img_avatar = ""
    if content_tag:
        first_img = content_tag.find("img")
        if first_img:
            img_avatar = first_img.get("data-original") or first_img.get("src") or ""
            if img_avatar.startswith("//"):  # type: ignore
                img_avatar = "https:" + img_avatar  # type: ignore

    date = ""
    blogbody = soup.find("div", class_="blogbody")
    if blogbody:
        for node in blogbody.children:
            if isinstance(node, Comment):
                m = re.search(r'dc:date="([^"]+)"', node)
                if m:
                    date = m.group(1)  # already ISO 8601, use as-is
                    break
    if not date:
        date_tag = soup.find("span", class_="entrydate", itemprop="datePublished")
        date_raw = (
            date_tag.get("content") or date_tag.get_text(strip=True) if date_tag else ""
        )
        ts = parse_date_to_timestamp(date_raw)  # type: ignore
        date = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""

    categories: list[str] = []
    category_tag = soup.find("p", id="category-right")
    if category_tag:
        categories = [
            a.get_text(strip=True)
            for a in category_tag.find_all("a", class_="aposted")
            if a.get_text(strip=True)
        ]

    company_name = ""
    address = ""
    official_site = ""

    h5_tag = soup.find("h5")
    if h5_tag:
        # Extract company name from the direct text nodes in <h5>
        company_name = "".join(
            node.strip()
            for node in h5_tag.children
            if isinstance(node, NavigableString)
        ).strip()

        span_tag = h5_tag.find("span")
        if span_tag:
            # Extract the address by reading text until the first <br>
            address_parts = []
            for child in span_tag.children:
                if getattr(child, "name", None) == "br":
                    break

                if isinstance(child, NavigableString):
                    text = child.strip()
                    if text:
                        address_parts.append(text)

            address = "".join(address_parts).strip()

            # Remove prefix "本社：" if present
            if address.startswith("本社："):
                address = address.removeprefix("本社：").strip()

            # Official site
            a_tag = span_tag.find("a", href=True)
            if a_tag:
                official_site = a_tag["href"].strip()

    if not title and not content_html:
        log_utils.warning(f"No title or content found for {url}")
        return None

    return {
        "url": url,
        "title": title,
        "date": date,
        "content": content_html,
        "img_avatar": img_avatar,
        "categories": categories,
        "company_name": company_name,
        "address": address,
        "official_site": official_site,
    }


def run_crawl(urls: list[str]) -> dict:

    total = len(urls)
    success = 0
    failed = 0

    for index, url in enumerate(urls, start=1):
        log_utils.info(f"[{index}/{total}] Crawling {url}")

        article = crawl_article(url)

        if article is None:
            failed += 1
            continue

        try:
            save_ceo_interview(article)

            success += 1

            log_utils.info(f"[{index}/{total}] Saved")

        except Exception as e:
            failed += 1
            log_utils.error(f"Failed to run crawl: {e}")

    return {"total": total, "success": success, "failed": failed}


# local test
# if __name__ == "__main__":
#     run_crawl()
