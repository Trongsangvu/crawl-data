import json
import os

import boto3

from crawler_index import crawl_index
from utils.log_utils import crawler

s3 = boto3.client("s3")
sfn = boto3.client("stepfunctions")

BUCKET = "vision-match-ceo-crawler"
KEY = "crawler/article_urls.json"

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]


def lambda_handler(event, context):
    try:
        crawler("Start crawler index")

        records = crawl_index()

        crawler(f"Found {len(records)} articles")

        # Upload article_urls.json lên S3
        s3.put_object(
            Bucket=BUCKET,
            Key=KEY,
            Body=json.dumps(records, ensure_ascii=False),
            ContentType="application/json",
        )

        crawler("Upload article_urls.json to S3 success")

        # Trigger Step Functions
        response = sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(
                {
                    "bucket": BUCKET,
                    "key": KEY,
                }
            ),
        )

        crawler(f"Step Functions started: {response['executionArn']}")

        return {
            "statusCode": 200,
            "body": {
                "count": len(records),
                "bucket": BUCKET,
                "key": KEY,
                "executionArn": response["executionArn"],
            },
        }

    except Exception as e:
        crawler(f"Index failed: {e}")
        raise
