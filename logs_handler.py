#!/usr/bin/env python3
"""Rotating log handler with emoji‑enriched output."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from global_const import LOG_DIR, ANSI

LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str, log_file: str = "logs/system.log") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler with ANSI colors
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(f'{ANSI["CYAN"]}%(asctime)s{ANSI["RESET"]} - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def log_event(logger: logging.Logger, message: str, level: str = "info"):
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.debug(message)