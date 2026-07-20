"""Utility helpers for colored console logging."""

import traceback
from datetime import datetime


class BColors:
    """ANSI color codes for terminal output."""

    WARNING = "\033[93m"
    ENDC = "\033[0m"

    CRED = "\33[31m"
    C_BLUE = "\33[34m"
    C_GREEN = "\33[32m"


def warning(message):
    """Print a yellow warning message."""
    print(f"{BColors.WARNING}WARNING: {message}{BColors.ENDC}", flush=True)


def error(message: str):
    """Print a red error message."""
    print(f"{BColors.CRED}ERROR: {message}{BColors.ENDC}", flush=True)


def info(message: str):
    """Print a green info message."""
    print(f"{BColors.C_GREEN}INFO: {message}{BColors.ENDC}", flush=True)


def crawler(message: str):
    """Print a single-line blue crawler progress message."""
    print(f"{BColors.C_BLUE}[crawler] {message}{BColors.ENDC}", flush=True)


def logger(file_name: str, function: str, message: str):
    """Print a structured error log with file, function, message, and timestamp."""
    print(f"{BColors.CRED}FILE: {file_name}{BColors.ENDC}", flush=True)
    print(f"{BColors.CRED}FUNCTION: {function}{BColors.ENDC}", flush=True)
    print(f"{BColors.CRED}ERROR: {message}{BColors.ENDC}", flush=True)
    print(
        f"{BColors.CRED}TIME: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}{BColors.ENDC}",
        flush=True,
    )


def log_exception(exception: Exception):
    """Log an exception with file, function, and message extracted from the traceback."""
    formatted_lines = traceback.format_exc().splitlines()
    e = formatted_lines[1].strip().split(",")
    logger(
        file_name=(e[0] + e[1]).replace("File", "").strip(),
        function=e[-1].replace(" in", "").strip(),
        message=exception.__str__(),
    )
