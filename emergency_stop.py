#!/usr/bin/env python3
"""Emergency Stop – Kill all background processes and Flask server."""

import os
import signal
import sys
import time
import psutil

PID_FILE = "nexus.pid"

def stop_all():
    if not os.path.exists(PID_FILE):
        print("⚠️ No PID file found. Is the system running?")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            print(f"🔪 Terminating child PID {child.pid}")
            child.terminate()
        parent.terminate()
        print("💀 NEXUS-CYBER-RUNNER V3 terminated")
    except psutil.NoSuchProcess:
        print("Process already dead")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

if __name__ == "__main__":
    stop_all()
    sys.exit(0)