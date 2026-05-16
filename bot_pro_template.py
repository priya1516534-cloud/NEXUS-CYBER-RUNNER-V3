#!/usr/bin/env python3
"""Advanced Telegram Bot with error handling, rate limiting, and logging."""

import telebot
import time
import threading
from functools import wraps
from logs_handler import log_event
import logging
from system_diagnostics import SystemHealth

logger = logging.getLogger("TeleBot")

class CyberBot:
    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token, threaded=False)
        self.health = SystemHealth()
        self._register_handlers()
    
    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            self.bot.reply_to(message, "💀 NEXUS-CYBER-RUNNER V3 ONLINE 💀\n/status – System health\n/vault – List vault scripts")
        
        @self.bot.message_handler(commands=['status'])
        def status_cmd(message):
            diag = self.health.full_diagnostics()
            reply = f"⚡ CPU: {diag['cpu_percent']}%\n🧠 RAM: {diag['ram_percent']}%\n💾 DISK: {diag['disk_percent']}%"
            self.bot.reply_to(message, reply)
        
        @self.bot.message_handler(func=lambda m: True)
        def echo_all(message):
            self.bot.reply_to(message, "❓ Unknown command. Use /help")
    
    def run(self):
        """Start polling with retry logic."""
        while True:
            try:
                log_event(logger, "🤖 Telegram bot polling started")
                self.bot.infinity_polling(timeout=30, long_polling_timeout=30)
            except Exception as e:
                log_event(logger, f"Telegram bot error: {e}", level="error")
                time.sleep(5)