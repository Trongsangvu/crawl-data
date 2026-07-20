# CEO Interview Crawler - AWS Lambda

Crawler service for collecting CEO interview articles from `shacho.osakazine.net` and sending data to the backend API.

---

# Architecture

```
EventBridge Scheduler
        |
        v
AWS Lambda
        |
        v
FastAPI Crawler API
        |
        v
Crawler
        |
        v
MongoDB
```

For local testing:

```
AWS Lambda
      |
      v
ngrok / Cloudflare Tunnel
      |
      v
FastAPI (localhost:8000)
      |
      v
Crawler
```

---

# Project Structure

```
lambda-crawler/
│
├── lambda_function.py       # Lambda entry point
├── crawler_index.py         # Collect article URLs
├── main.py                  # Crawl article details
│
├── integrations/
│   └── app_client.py        # Backend API client
│
├── utils/
│   └── log_utils.py         # Logger
│
├── requirements.txt
│
└── README.md
```

---

# Features

- Crawl CEO interview article URLs

- Crawl article detail:
  - Title
  - Content
  - Published date
  - Company name
  - Address
  - Official website
  - Categories
  - Avatar image

- Send crawled data to backend API

- Run automatically with AWS EventBridge Scheduler

---

# Requirements

## Runtime

AWS Lambda:

```
Python 3.12
```

Local:

```
Python >= 3.12
```

---

# Environment Variables

Lambda requires:

```env
API_URL=https://your-api-domain.com
```

Example:

```env
API_URL=https://api.example.com
```

---

# Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run crawler locally:

```bash
python lambda_function.py
```

or:

```bash
python -c "from lambda_function import lambda_handler; print(lambda_handler({}, {}))"
```

---

# Test Lambda with Local API

## 1. Start FastAPI locally

Example:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

API:

```
http://localhost:8000
```

---

## 2. Create public tunnel

### Option 1: ngrok

Install and run:

```bash
ngrok http 8000
```

Example output:

```
https://xxxx.ngrok-free.app
```

Update Lambda environment:

```env
API_URL=https://xxxx.ngrok-free.app
```

---

### Option 2: Cloudflare Tunnel

Run:

```bash
cloudflared tunnel --url http://localhost:8000
```

Example:

```
https://xxxx.trycloudflare.com
```

Update:

```env
API_URL=https://xxxx.trycloudflare.com
```

---

## 3. Execute Lambda Test

AWS Console:

```
Lambda
  -> Test
  -> Create Test Event
  -> Invoke
```

Expected response:

```json
{
  "statusCode": 200,
  "body": {
    "message": "Crawler completed successfully"
  }
}
```

---

# Lambda Deployment

There are two deployment methods.

---

# Option 1: Upload ZIP directly

Use when dependencies are small.

## Install dependencies

```bash
pip install \
-r requirements.txt \
-t build \
--platform manylinux2014_x86_64 \
--implementation cp \
--python-version 3.12 \
--only-binary=:all:
```

## Create ZIP

```bash
cd build

zip -r ../lambda.zip .
```

## Upload

AWS Console:

```
AWS Lambda
 -> Code
 -> Upload from .zip file
```

---

# Option 2: Lambda Layer (Recommended)

Use Lambda Layer for dependencies.

Benefits:

- Keep Lambda code package small
- Reuse dependencies between functions
- Easier dependency updates
- Avoid package size limitations

---

## 1. Create Layer folder

Lambda Python Layer requires:

```
layer/
└── python/
    ├── requests
    ├── bs4
    ├── lxml
    └── dependencies
```

Create:

```bash
mkdir -p layer/python
```

---

## 2. Install dependencies into Layer

```bash
pip install \
-r requirements.txt \
-t layer/python \
--platform manylinux2014_x86_64 \
--implementation cp \
--python-version 3.12 \
--only-binary=:all:
```

Result:

```
layer/
└── python/
    ├── requests
    ├── urllib3
    ├── bs4
    ├── lxml
    └── ...
```

---

## 3. Create Layer ZIP

```bash
cd layer

zip -r ../crawler-dependencies-layer.zip python
```

Output:

```
crawler-dependencies-layer.zip
```

---

## 4. Upload Lambda Layer

AWS Console:

```
AWS Lambda
 -> Layers
 -> Create layer
```

Configuration:

```
Layer name:
crawler-dependencies

Upload:
crawler-dependencies-layer.zip

Compatible runtime:
Python 3.12
```

Create layer.

---

## 5. Attach Layer to Lambda Function

AWS Console:

```
AWS Lambda
 -> Function
 -> Layers
 -> Add a layer
```

Select:

```
Custom layers
 -> crawler-dependencies
 -> Add
```

After attaching:

```
Lambda Function

/
├── lambda_function.py
├── crawler_index.py
├── main.py

/opt/python
├── requests
├── bs4
├── lxml
└── dependencies
```

Python can import normally:

```python
import requests
from bs4 import BeautifulSoup
```

---

# Deploy Lambda Code With Layer

When using Layer, upload only source code.

Create ZIP:

```bash
zip lambda-code.zip \
lambda_function.py \
crawler_index.py \
main.py \
-r integrations \
-r utils
```

Upload:

```
AWS Lambda
 -> Code
 -> Upload from .zip file
```

---

# Update Dependencies Layer

When `requirements.txt` changes:

Remove old layer:

```bash
rm -rf layer
```

Create again:

```bash
mkdir -p layer/python
```

Install:

```bash
pip install \
-r requirements.txt \
-t layer/python \
--platform manylinux2014_x86_64 \
--implementation cp \
--python-version 3.12 \
--only-binary=:all:
```

Zip:

```bash
cd layer

zip -r ../crawler-dependencies-layer.zip python
```

Create new Layer version:

```
AWS Lambda
 -> Layers
 -> Create new version
```

Update function:

```
Lambda
 -> Layers
 -> Replace layer version
```

---

# Temporary Storage

Lambda filesystem is read-only except `/tmp`.

Use:

```python
OUTPUT_FILE = "/tmp/article_urls.json"
```

Do not write:

```
/var/task
```

because Lambda will throw:

```
Read-only file system
```

---

# Scheduler

EventBridge uses UTC timezone.

Example:

Vietnam time:

```
06:00 AM GMT+7
```

Convert:

```
23:00 UTC previous day
```

Cron:

```
cron(0 23 * * ? *)
```

---

# Logging

CloudWatch Logs:

```
AWS Console
 -> Lambda
 -> Monitor
 -> View CloudWatch logs
```

Example:

```
INFO [392/400] Crawling article
INFO Saved article
ERROR Failed URL
```

---

# Troubleshooting

## Lambda timeout

Problem:

```
Task timed out after 900 seconds
```

Cause:

- Too many articles
- Sequential crawling

Solution:

- Split crawler jobs
- Use Step Functions
- Use SQS queue
- Increase Lambda memory
- Run crawler in parallel

---

## Cannot import package

Example:

```
ModuleNotFoundError
```

Check:

- Python version
- Lambda architecture
- manylinux package
- Layer attached correctly

---

## lxml import error

Example:

```
cannot import name etree from lxml
```

Solution:

Build Layer using:

```
Python 3.12
manylinux2014_x86_64
```

Do not build using local Windows/macOS binaries.

---

## API Unauthorized

Check:

```env
API_URL
```

and API authentication headers.

---

## Local API cannot be reached

Check:

### FastAPI binding

Wrong:

```bash
uvicorn main:app
```

Correct:

```bash
uvicorn main:app --host 0.0.0.0
```

Check:

1. Tunnel URL
2. Lambda environment variable
3. Firewall/network settings

---

# Future Improvements

- Replace Lambda crawler with Step Functions
- Parallel crawl using SQS
- Add retry mechanism
- Store crawl progress
- Avoid crawling duplicated articles
- Add crawler monitoring dashboard
- Add distributed crawling workers
