#!/usr/bin/env python3
"""AutoCleaner – Scheduled deletion of logs, cache, and temp files."""

import os
import time
import shutil
import threading
from pathlib import Path
from datetime import datetime, timedelta
from logs_handler import log_event
import logging
from global_const import LOG_DIR, CACHE_DIR

logger = logging.getLogger("AutoCleaner")

class AutoCleaner:
    def __init__(self, interval_sec: int = 3600):
        self.interval = interval_sec
        self.log_dir = Path(LOG_DIR)
        self.cache_dir = Path(CACHE_DIR)
        self.log_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
    
    def clean_old_logs(self, days=7):
        cutoff = datetime.now() - timedelta(days=days)
        for log_file in self.log_dir.glob("*.log"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
                log_file.unlink()
                log_event(logger, f"🧹 Deleted old log: {log_file.name}")
    
    def clean_cache(self):
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir()
            log_event(logger, "🗑️ Cache directory purged")
    
    def run(self, stop_event: threading.Event):
        while not stop_event.is_set():
            self.clean_old_logs()
            self.clean_cache()
            # Sleep with interruptible wait
            for _ in range(self.interval):
                if stop_event.is_set():
                    break
                time.sleep(1)
        log_event(logger, "🛑 AutoCleaner stopped")