#!/usr/bin/env python3
"""NetworkOptimizer – Ping stability, connection checks, auto‑retry."""

import subprocess
import time
import threading
import platform
from logs_handler import log_event
import logging

logger = logging.getLogger("NetOpt")

class NetworkOptimizer:
    def __init__(self):
        self.ping_loss = 0
        self.latency_ms = 0
    
    def ping_host(self, host="8.8.8.8", count=4):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        cmd = ['ping', param, str(count), host]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract loss/latency (simplified)
                log_event(logger, f"🌐 Ping to {host} successful")
                return True
        except Exception as e:
            log_event(logger, f"Ping failed: {e}", level="error")
        return False
    
    def optimize_loop(self, stop_event: threading.Event):
        while not stop_event.is_set():
            ok = self.ping_host()
            if not ok:
                log_event(logger, "⚠️ Network instability detected", level="warning")
            time.sleep(60)
    
    def status(self):
        return {"ping_success": self.ping_host()}