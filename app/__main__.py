#!/usr/bin/env python3

from dotenv import load_dotenv
import logging
from typing import Optional

from app.config import configure_logging, configure_sentry, check_env
from refresh import refresh_balances


def main() -> None:
    try:
        load_dotenv()       # Load .env if present (development convenience)
        configure_logging() # Set up Python logging
        configure_sentry()  # Optional Sentry integration
        check_env()         # Ensure environment is correct

        refresh_balances()

    except Exception as exc:
        logging.exception("Fatal error in main")
        raise  # ensure a non-zero exit code


if __name__ == "__main__":
    main()
