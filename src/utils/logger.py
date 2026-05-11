import logging
import os
from datetime import datetime


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """Set up a logger with console and file handlers"""

    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))

    # File handler
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"{log_dir}/agent_{timestamp}.log")
    file_handler.setLevel(getattr(logging, level))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
