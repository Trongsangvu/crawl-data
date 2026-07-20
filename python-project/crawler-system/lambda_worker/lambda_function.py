from main import run_crawl


def lambda_handler(event, context):

    batch_id = event["batch_id"]

    urls = event["urls"]

    result = run_crawl(batch_id, urls)

    return {"batch_id": batch_id, "processed": len(urls), "result": result}
