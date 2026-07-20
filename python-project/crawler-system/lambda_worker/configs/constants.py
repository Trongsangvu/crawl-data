import os

class APIConfig:
    """Configuration for the internal API integration."""

    API_BASE_URL = os.getenv(
        "API_BASE_URL",
        "http://127.0.0.1:8000",
    )

    API_KEY = os.getenv(
        "API_KEY",
        "",
    )

# UTC: cron(0 13,15,21 * * ? *)
# EventBridge Scheduler timezone = Asia/Tokyo: cron(0 0,6,22 * * ? *)
