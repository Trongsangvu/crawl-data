import json
import os
import boto3

s3 = boto3.client("s3")

BUCKET = os.environ["S3_BUCKET"]
KEY = os.environ["S3_KEY"]

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))


def lambda_handler(event, context):

    response = s3.get_object(Bucket=BUCKET, Key=KEY)

    records = json.loads(response["Body"].read())

    # urls = [item["url"] for item in records]
    urls = [r["url"] for r in records if r["status"] in ("not_crawled", "failed")]

    batches = []

    for i in range(0, len(urls), BATCH_SIZE):

        batches.append(
            {"batch_number": len(batches) + 1, "urls": urls[i : i + BATCH_SIZE]}
        )

    print(f"Total URLs: {len(urls)}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Total Batch: {len(batches)}")

    return {"batches": batches}
