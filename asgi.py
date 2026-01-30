import logging

from src.backend.utils.logger import setup_logging
from src.backend.http.app import create_app

setup_logging(level=logging.INFO, console_level=logging.INFO, log_to_file=True)

app = create_app()
