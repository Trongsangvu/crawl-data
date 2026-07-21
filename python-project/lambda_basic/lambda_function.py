from crawler_index import crawl_index
from main import run_crawl
from s3_manager import download_records, upload_records


def lambda_handler(event, context):
    try:
        download_records()

        crawl_index()

        run_crawl(context)

        upload_records()

        return {
            "statusCode": 200,
            "body": {
                "message": "Crawler completed successfully",
            },
        }

    except Exception as e:
        print(f"Error: {e}")
        raise
