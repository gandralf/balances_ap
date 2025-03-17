import logging
import os
from typing import List, Optional
import sentry_sdk


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def configure_sentry() -> None:
    dsn: Optional[str] = os.getenv('SENTRY_DSN')
    if dsn:
        logging.info('Configuring Sentry.')
        sentry_sdk.init(dsn=dsn)
    else:
        logging.warning('Sentry not configured: SENTRY_DSN not set.')


def check_env() -> None:
    required_env: List[str] = ['SFTP_URL', 'SFTP_USERNAME', 'SFTP_PASSWORD', 'RABBITMQ_URL']
    missing: List[str] = [v for v in required_env if not os.getenv(v)]
    if len(missing):
        raise EnvironmentError(f"Missing required env vars: {missing}")


