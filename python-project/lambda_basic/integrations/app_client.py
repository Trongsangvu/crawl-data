"""API client for saving crawled CEO interview data."""

from typing import List, Optional

import requests
from pydantic import BaseModel, AnyHttpUrl

from utils import log_utils
from configs.constants import APIConfig

CEO_INTERVIEWS_ENDPOINT = f"{APIConfig.API_BASE_URL}/api/v1/ceo-interviews/"
CHECK_BULK_ENDPOINT = f"{APIConfig.API_BASE_URL}/api/v1/ceo-interviews/check-bulk"


class CeoInterviewCreateRequest(BaseModel):
    url: AnyHttpUrl
    posted_date: Optional[str] = None
    title: Optional[str] = None
    content_html: Optional[str] = None
    img_avatar: Optional[str] = None
    categories: List[str] = []
    company_name: Optional[str] = None
    address: Optional[str] = None
    official_site: Optional[str] = None


def check_existing_urls(urls: List[str]) -> tuple[set, Optional[str]]:
    if not urls:
        return set(), None

    existing_urls_set = set()
    latest_date_db = None
    chunk_size = 500

    for i in range(0, len(urls), chunk_size):
        chunk = urls[i:i + chunk_size]
        try:
            response = requests.post(
                CHECK_BULK_ENDPOINT,
                headers={"X-API-KEY": APIConfig.API_KEY},
                json={"urls": chunk},
                timeout=15,
            )
            response.raise_for_status()
            res_data = response.json()

            payload = res_data.get("data", res_data)

            # Gather existing urls
            batch_existing = payload.get("existing_urls", [])
            existing_urls_set.update(batch_existing)

            # Get lasted_date
            if payload.get("latest_date"):
                latest_date_db = payload.get("latest_date")

        except requests.RequestException as e:
            log_utils.error(f"Failed to check bulk URLs (chunk {i}): {e}")

    return existing_urls_set, latest_date_db


def save_ceo_interview(article: dict) -> bool:
    payload = CeoInterviewCreateRequest(
        url=article["url"],
        posted_date=article.get("date"),
        title=article.get("title"),
        content_html=article.get("content"),
        img_avatar=article.get("img_avatar"),
        categories=article.get("categories", []),
        company_name=article.get("company_name"),
        address=article.get("address"),
        official_site=article.get("official_site"),
    )

    try:
        response = requests.post(
            CEO_INTERVIEWS_ENDPOINT,
            headers={
                "x-api-key": APIConfig.API_KEY,
            },
            json=payload.model_dump(mode="json"),
            timeout=30,
        )

        response.raise_for_status()

        log_utils.info(f"Saved {article['url']} ({response.status_code})")

        return True

    except requests.RequestException as e:
        log_utils.error(f"Failed {article['url']} : {e}")
        return False
