#!/usr/bin/env python3
"""TaskLoop – Continuous automation loops (scraping, health checks, etc.)."""

import time
import threading
import random
from logs_handler import log_event
import logging
from api_gateway import FreeFireGateway
from system_diagnostics import SystemHealth

logger = logging.getLogger("TaskLoop")

class TaskLoop:
    def __init__(self):
        self.tasks = []
        self.running_tasks = {}
        self.ff_gw = FreeFireGateway({})
        self.health = SystemHealth()
    
    def scrape_news(self):
        """Example: fetch dummy news or stats."""
        log_event(logger, "📰 Scraping cyber news feed...")
        # Simulate work
        time.sleep(1)
        return "News: Matrix glitch in sector 7"
    
    def health_ping(self):
        diag = self.health.full_diagnostics()
        log_event(logger, f"❤️ Health ping: CPU {diag['cpu_percent']}% RAM {diag['ram_percent']}%")
    
    def run(self, stop_event: threading.Event):
        """Main loop executing tasks defined in config."""
        task_registry = {
            "scrape_news": self.scrape_news,
            "health_ping": self.health_ping
        }
        while not stop_event.is_set():
            for task_name, func in task_registry.items():
                if stop_event.is_set():
                    break
                try:
                    func()
                except Exception as e:
                    log_event(logger, f"Task {task_name} failed: {e}", level="error")
                time.sleep(5)  # delay between tasks
            time.sleep(30)  # cycle interval
        log_event(logger, "🛑 TaskLoop stopped")
    
    def active_tasks(self):
        return list(self.running_tasks.keys())