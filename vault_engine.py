#!/usr/bin/env python3
"""
VAULT ENGINE – Auto‑discover, manage, and execute scripts from VAULT folder.
Supports dynamic import, threading, and subprocess execution.
"""

import os
import sys
import time
import threading
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Any
from global_const import VAULT_DIR, LOG_DIR
from logs_handler import log_event
import logging

logger = logging.getLogger("VaultEngine")

class VaultManager:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(exist_ok=True)
        self.active_scripts: Dict[str, threading.Thread] = {}
        self.script_status: Dict[str, str] = {}
        
    def discover_scripts(self) -> List[Path]:
        """Return all executable scripts in vault."""
        scripts = []
        for ext in ['*.py', '*.sh']:
            scripts.extend(self.vault_path.glob(ext))
        return scripts
    
    def load_python_module(self, script_path: Path):
        """Dynamically import a Python script and return its main function if exists."""
        module_name = script_path.stem
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'main'):
                return module.main
            elif hasattr(module, 'run'):
                return module.run
        return None
    
    def run_script(self, script_name: str, async_mode: bool = True) -> Any:
        """Execute a script (Python or shell) synchronously or asynchronously."""
        script_path = self.vault_path / script_name
        if not script_path.exists():
            return f"❌ Script {script_name} not found"
        
        if script_path.suffix == '.py':
            func = self.load_python_module(script_path)
            if func:
                if async_mode:
                    t = threading.Thread(target=func, daemon=True)
                    t.start()
                    self.active_scripts[script_name] = t
                    self.script_status[script_name] = "running"
                    return f"▶️ Async started {script_name}"
                else:
                    return func()
            else:
                return f"⚠️ No main() or run() in {script_name}"
        elif script_path.suffix == '.sh':
            cmd = ["bash", str(script_path)]
            if async_mode:
                threading.Thread(target=lambda: subprocess.run(cmd), daemon=True).start()
                return f"🐚 Async shell: {script_name}"
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.stdout
        return "❌ Unsupported script type"
    
    def auto_start_scripts(self, stop_event: threading.Event):
        """Continuously watch vault and auto‑start new scripts based on config."""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class VaultHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith(('.py', '.sh')):
                    name = Path(event.src_path).name
                    log_event(logger, f"📂 New script detected: {name}, auto‑starting...")
                    self.manager.run_script(name, async_mode=True)
        
        handler = VaultHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.vault_path), recursive=False)
        observer.start()
        
        # Also start existing scripts marked for auto
        for script in self.discover_scripts():
            log_event(logger, f"🔁 Auto‑starting {script.name}")
            self.run_script(script.name, async_mode=True)
        
        while not stop_event.is_set():
            time.sleep(2)
        observer.stop()
        observer.join()
    
    def get_status(self) -> dict:
        return {
            "total_scripts": len(self.discover_scripts()),
            "active_scripts": len([t for t in self.active_scripts.values() if t.is_alive()]),
            "status_map": self.script_status
        }