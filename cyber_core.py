#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║                 NEXUS-CYBER-RUNNER V3 – CORE ENGINE                 ║
║  Flask + Multi‑threading + Auto‑dependency + Real‑time logs        ║
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
from importlib import metadata  # <--- pkg_resources ki jagah ye use hoga

from flask import Flask, render_template, request, jsonify, Response, stream_with_context

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

# ------------------------ AUTO DEPENDENCY RESOLVER (FIXED) ------------
def auto_install_dependencies():
    """Scans imports and installs missing packages without pkg_resources."""
    missing_pkgs = set()
    
    # Modern way to get installed packages
    installed = {dist.metadata['Name'].lower() for dist in metadata.distributions()}
    
    project_files = list(Path(".").glob("*.py")) + list(Path(".").glob("*/*.py"))
    
    for py_file in project_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        pkg = alias.name.split('.')[0].lower()
                        if pkg not in installed:
                            missing_pkgs.add(pkg)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        pkg = node.module.split('.')[0].lower()
                        if pkg not in installed:
                            missing_pkgs.add(pkg)
        except Exception as e:
            log_event(logger, f"⚠️ AST parse error in {py_file}: {e}", level="warning")
    
    # Kuch common mapping (agar import name aur pip name alag ho)
    mapping = {"telebot": "pyTelegramBotAPI", "bs4": "beautifulsoup4"}
    
    if missing_pkgs:
        for pkg in missing_pkgs:
            real_pkg = mapping.get(pkg, pkg)
            # Standard libraries ko skip karne ke liye
            if real_pkg in ['os', 'sys', 'json', 'ast', 'threading', 'time', 'subprocess', 'logging', 'pathlib', 'importlib']:
                continue
                
            log_event(logger, f"📦 Auto‑installing: {real_pkg}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", real_pkg])
                log_event(logger, f"✅ Installed {real_pkg}")
            except Exception as e:
                log_event(logger, f"❌ Failed to install {real_pkg}: {e}", level="error")
    else:
        log_event(logger, "✅ All dependencies are satisfied")

# Run dependency resolver at startup
auto_install_dependencies()

# [Baki saara Flask aur Route ka code niche same rahega...]
# (Yahan se niche wala pura original code paste kar dena)
