#!/usr/bin/env python3
"""System Health – CPU, RAM, Network, Disk usage."""

import psutil
import platform
import subprocess
from logs_handler import log_event
import logging

logger = logging.getLogger("SysDiag")

class SystemHealth:
    @staticmethod
    def cpu_usage():
        return psutil.cpu_percent(interval=0.5)
    
    @staticmethod
    def ram_usage():
        mem = psutil.virtual_memory()
        return mem.percent
    
    @staticmethod
    def disk_usage(path="/"):
        disk = psutil.disk_usage(path)
        return disk.percent
    
    @staticmethod
    def network_health():
        net = psutil.net_io_counters()
        return {"bytes_sent": net.bytes_sent, "bytes_recv": net.bytes_recv, "packets_dropped": net.dropin}
    
    def full_diagnostics(self):
        diag = {
            "cpu_percent": self.cpu_usage(),
            "ram_percent": self.ram_usage(),
            "disk_percent": self.disk_usage(),
            "platform": platform.platform(),
            "network": self.network_health()
        }
        log_event(logger, f"📊 Diagnostics: {diag['cpu_percent']}% CPU, {diag['ram_percent']}% RAM")
        return diag