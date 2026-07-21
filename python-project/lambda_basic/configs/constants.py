import os


class APIConfig:
    """Configuration for the internal API integration."""

    API_BASE_URL = os.getenv(
        "API_BASE_URL",
        "https://rasping-chain-backspace.ngrok-free.dev",
    )

    API_KEY = os.getenv(
        "API_KEY",
        "",
    )


# cron(0 13,15,21 * * ? *)
