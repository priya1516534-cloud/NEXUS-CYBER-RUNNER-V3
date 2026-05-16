#!/usr/bin/env python3
"""Global constants, ANSI colors, paths for NEXUS-CYBER-RUNNER V3."""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.resolve()

# Directories
VAULT_DIR = PROJECT_ROOT / "VAULT"
LOG_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = PROJECT_ROOT / "cache"
CONFIG_DIR = PROJECT_ROOT

# ANSI escape codes for neon logging
ANSI = {
    "GREEN": "\033[92m",
    "CYAN": "\033[96m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "MAGENTA": "\033[95m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m"
}

# Emoji constants
EMOJI = {
    "ROCKET": "🚀",
    "SKULL": "💀",
    "GEAR": "⚙️",
    "FOLDER": "📂",
    "WARNING": "⚠️",
    "CHECK": "✅",
    "CROSS": "❌"
}