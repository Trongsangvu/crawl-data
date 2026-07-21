import os

import json
import boto3
import botocore

s3 = boto3.client("s3")

ARTICLE_URLS_FILE = "/tmp/article_urls.json"

BUCKET_NAME = os.environ["BUCKET_NAME"]
S3_KEY = "crawler/article_urls.json"


LOCAL_FILE = "/tmp/article_urls.json"


def download_records():

    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=S3_KEY)

        s3.download_file(BUCKET_NAME, S3_KEY, LOCAL_FILE)

        print(f"Downloaded s3://{BUCKET_NAME}/{S3_KEY}")

    except botocore.exceptions.ClientError as e:

        error_code = e.response["Error"]["Code"]

        if error_code == "404":

            print("No existing records. Creating new file.")

            with open(LOCAL_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        else:
            raise


def upload_records() -> None:
    s3.upload_file(
        ARTICLE_URLS_FILE,
        BUCKET_NAME,
        S3_KEY,
    )
