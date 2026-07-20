import json
import boto3

s3 = boto3.client("s3")


BATCH_SIZE = 50


def lambda_handler(event, context):

    bucket = event["bucket"]

    key = event["key"]

    response = s3.get_object(Bucket=bucket, Key=key)

    records = json.loads(response["Body"].read())

    urls = [item["url"] for item in records]

    batches = []

    for i in range(0, len(urls), BATCH_SIZE):

        batches.append(
            {"batch_id": i // BATCH_SIZE + 1, "urls": urls[i : i + BATCH_SIZE]}
        )

    return {"batches": batches}
