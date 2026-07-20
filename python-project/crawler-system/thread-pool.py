from concurrent.futures import ThreadPoolExecutor, as_completed


def process_url(index: int, total: int, url: str) -> bool:
    """Crawl and save a single article."""

    log_utils.info(f"[{index}/{total}] Crawling {url}")

    article = crawl_article(url)

    if article is None:
        log_utils.warning(f"[{index}/{total}] Failed")
        return False

    try:
        save_ceo_interview(article)
        log_utils.info(f"[{index}/{total}] Saved")
        return True

    except Exception as e:
        log_utils.error(f"[{index}/{total}] Failed: {e}")
        return False


def run_crawl(urls: list[str]) -> dict:
    total = len(urls)
    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_url, index, total, url): url
            for index, url in enumerate(urls, start=1)
        }

        for future in as_completed(futures):
            url = futures[future]

            try:
                if future.result():
                    success += 1
                else:
                    failed += 1

            except Exception as e:
                failed += 1
                log_utils.error(f"{url} crashed: {repr(e)}")

    return {
        "total": total,
        "success": success,
        "failed": failed,
    }
