"""API client for saving crawled CEO interview data."""

from typing import List, Optional

import requests
from pydantic import BaseModel, AnyHttpUrl

from utils import log_utils
from configs.constants import APIConfig

CEO_INTERVIEWS_ENDPOINT = f"{APIConfig.API_BASE_URL}/api/v1/ceo-interviews/"


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
