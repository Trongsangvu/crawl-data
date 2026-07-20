# Vision Match CEO Crawler System

AWS serverless crawler system for collecting CEO interview articles from `shacho.osakazine.net`.

The system is designed to avoid AWS Lambda 15-minute timeout by splitting the crawler into multiple Lambda functions managed by AWS Step Functions.

---

# Architecture

EventBridge
|
v
lambda-index
|
|
├── crawler_index.py
|
v
S3/article_urls.json
|
v
Step Functions
|
v
lambda-split
|
|
v
[
batch 50 urls
batch 50 urls
batch 50 urls
]
|
v
lambda-worker
|
|
├── main.py
├── app_client.py
└── utils
|
v
FastAPI
|
v
MongoDB
