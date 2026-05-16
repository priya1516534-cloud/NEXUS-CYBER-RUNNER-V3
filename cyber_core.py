#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║                 NEXUS-CYBER-RUNNER V3 – CORE ENGINE                 ║
║  Flask + Multi‑threading + AST auto‑dependency + Real‑time logs     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import ast
import queue
import time
import threading
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import pkg_resources

# ------------------------ PROJECT IMPORTS ----------------------------
from global_const import *
from logs_handler import setup_logger, log_event
from security_layer import ip_whitelist_required, basic_auth_required
from vault_engine import VaultManager
from auto_cleaner import AutoCleaner
from system_diagnostics import SystemHealth
from api_gateway import FreeFireGateway
from task_loop_v3 import TaskLoop
from network_optimizer import NetworkOptimizer
from nexus_banner import print_banner
from emergency_stop import EmergencyStop

# ------------------------ CONFIGURATION ------------------------------
CONFIG_PATH = "config_v3.json"
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

# ------------------------ LOGGER SETUP --------------------------------
logger = setup_logger("CyberCore", log_file=CONFIG["system"]["log_file"])
log_event(logger, "🚀 NEXUS-CYBER-RUNNER V3 boot sequence initiated", level="info")

# ------------------------ AUTO DEPENDENCY RESOLVER (AST BASED) --------
def auto_install_dependencies():
    """Scans all .py files in project, extracts imports, and installs missing packages."""
    missing_pkgs = set()
    installed = {pkg.key for pkg in pkg_resources.working_set}
    project_files = list(Path(".").glob("*.py")) + list(Path(".").glob("*/*.py"))
    
    for py_file in project_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        pkg = alias.name.split('.')[0]
                        if pkg not in installed:
                            missing_pkgs.add(pkg)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        pkg = node.module.split('.')[0]
                        if pkg not in installed:
                            missing_pkgs.add(pkg)
        except Exception as e:
            log_event(logger, f"⚠️ AST parse error in {py_file}: {e}", level="warning")
    
    if missing_pkgs:
        log_event(logger, f"📦 Auto‑installing missing deps: {missing_pkgs}")
        for pkg in missing_pkgs:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                log_event(logger, f"✅ Installed {pkg}")
            except Exception as e:
                log_event(logger, f"❌ Failed to install {pkg}: {e}", level="error")
    else:
        log_event(logger, "✅ All dependencies are satisfied")

# Run dependency resolver at startup
auto_install_dependencies()

# ------------------------ FLASK APP INIT ------------------------------
app = Flask(__name__, template_folder=".")
app.config['SECRET_KEY'] = CONFIG["system"]["secret_key"]

# ------------------------ GLOBAL BACKGROUND SERVICES ------------------
message_queue = queue.Queue()          # real-time log stream
vault_mgr = VaultManager(CONFIG["vault"]["directory"])
auto_clean = AutoCleaner(CONFIG["cleaner"]["interval_seconds"])
health = SystemHealth()
freefire_api = FreeFireGateway(CONFIG.get("freefire", {}))
task_loop = TaskLoop()
net_opt = NetworkOptimizer()
stop_signal = threading.Event()

# ------------------------ REAL-TIME LOG FEED --------------------------
def log_to_queue(msg: str, level="info"):
    """Inject logs into the SSE queue."""
    timestamp = time.strftime("%H:%M:%S")
    message_queue.put(f"[{timestamp}] [{level.upper()}] {msg}")

# Patch global logger to also feed the queue
original_emit = logger.handlers[0].emit if logger.handlers else None
class QueueHandler(logging.Handler):
    def emit(self, record):
        log_msg = self.format(record)
        log_to_queue(log_msg, record.levelname)
if logger.handlers:
    logger.addHandler(QueueHandler())

# ------------------------ FLASK ROUTES ---------------------------------
@app.route('/')
@ip_whitelist_required
@basic_auth_required
def dashboard():
    """Serve the cyberpunk dashboard."""
    return render_template("index_dashboard.html")

@app.route('/api/logs')
@ip_whitelist_required
def stream_logs():
    """Server‑Sent Events endpoint for real‑time terminal logs."""
    def event_stream():
        while not stop_signal.is_set():
            try:
                msg = message_queue.get(timeout=1)
                yield f"data: {msg}\n\n"
            except queue.Empty:
                continue
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

@app.route('/api/status')
@ip_whitelist_required
def system_status():
    """Return CPU, RAM, network, and vault status."""
    diag = health.full_diagnostics()
    vault_status = vault_mgr.get_status()
    return jsonify({
        "diagnostics": diag,
        "vault": vault_status,
        "active_tasks": task_loop.active_tasks(),
        "network_optimizer": net_opt.status()
    })

@app.route('/api/files', methods=['GET', 'POST', 'DELETE', 'PUT'])
@ip_whitelist_required
@basic_auth_required
def file_manager():
    """Advanced file handling: list, upload, delete, edit."""
    vault_dir = Path(CONFIG["vault"]["directory"])
    vault_dir.mkdir(exist_ok=True)
    
    if request.method == 'GET':
        files = []
        for f in vault_dir.iterdir():
            if f.is_file():
                files.append({"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime})
        return jsonify(files)
    
    elif request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        save_path = vault_dir / file.filename
        file.save(save_path)
        log_to_queue(f"📁 File uploaded: {file.filename}")
        return jsonify({"message": f"Uploaded {file.filename}"})
    
    elif request.method == 'DELETE':
        filename = request.json.get('filename')
        if not filename:
            return jsonify({"error": "Missing filename"}), 400
        target = vault_dir / filename
        if target.exists():
            target.unlink()
            log_to_queue(f"🗑️ Deleted: {filename}")
            return jsonify({"message": f"Deleted {filename}"})
        return jsonify({"error": "File not found"}), 404
    
    elif request.method == 'PUT':
        data = request.json
        filename = data.get('filename')
        content = data.get('content')
        if not filename or content is None:
            return jsonify({"error": "Missing filename or content"}), 400
        target = vault_dir / filename
        target.write_text(content, encoding='utf-8')
        log_to_queue(f"✏️ Edited: {filename}")
        return jsonify({"message": f"Updated {filename}"})

@app.route('/api/run_vault_script', methods=['POST'])
@ip_whitelist_required
def run_vault_script():
    """Manually trigger a script from vault."""
    script_name = request.json.get('script')
    if not script_name:
        return jsonify({"error": "No script name"}), 400
    result = vault_mgr.run_script(script_name, async_mode=False)
    return jsonify({"result": result})

# ------------------------ BACKGROUND THREADS --------------------------
def background_worker():
    """Start all core background processes with threading."""
    # Vault auto‑startup
    vault_thread = threading.Thread(target=vault_mgr.auto_start_scripts, args=(stop_signal,), daemon=True)
    vault_thread.start()
    
    # Auto cleaner
    cleaner_thread = threading.Thread(target=auto_clean.run, args=(stop_signal,), daemon=True)
    cleaner_thread.start()
    
    # Task loop (continuous automation)
    task_thread = threading.Thread(target=task_loop.run, args=(stop_signal,), daemon=True)
    task_thread.start()
    
    # Network optimizer pinger
    net_thread = threading.Thread(target=net_opt.optimize_loop, args=(stop_signal,), daemon=True)
    net_thread.start()
    
    # Telegram bot (if token provided)
    if CONFIG.get("telegram", {}).get("bot_token"):
        from bot_pro_template import CyberBot
        bot = CyberBot(CONFIG["telegram"]["bot_token"])
        bot_thread = threading.Thread(target=bot.run, daemon=True)
        bot_thread.start()
        log_to_queue("🤖 Telegram bot activated")
    
    log_to_queue("💎 All background systems online")
    
    # Keep alive until stop signal
    while not stop_signal.is_set():
        time.sleep(1)

# ------------------------ EMERGENCY STOP REGISTRATION -----------------
emergency = EmergencyStop()
emergency.register_pid()
emergency.set_stop_callback(lambda: stop_signal.set())

# ------------------------ ENTRY POINT ---------------------------------
if __name__ == '__main__':
    print_banner()
    # Start background threads
    worker_thread = threading.Thread(target=background_worker, daemon=True)
    worker_thread.start()
    
    # Run Flask with multi‑threaded server
    app.run(host=CONFIG["system"]["host"],
            port=CONFIG["system"]["port"],
            threaded=True,
            debug=CONFIG["system"]["debug"])