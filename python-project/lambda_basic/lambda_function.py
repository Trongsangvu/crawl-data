from crawler_index import crawl_index
from main import run_crawl


def lambda_handler(event, context):
    try:
        crawl_index()
        run_crawl()

        return {
            "statusCode": 200,
            "body": {
                "message": "Crawler completed successfully",
            },
        }

    except Exception as e:
        print(f"Error: {e}")
        raise
