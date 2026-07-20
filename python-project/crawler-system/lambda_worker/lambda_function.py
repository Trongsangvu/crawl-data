from main import run_crawl

from utils import log_utils


def lambda_handler(event, context):

    urls = event["urls"]

    log_utils.info(f"Worker started with {len(urls)} URLs")

    result = run_crawl(urls)

    log_utils.info(f"Crawl result: {result}")

    return result
