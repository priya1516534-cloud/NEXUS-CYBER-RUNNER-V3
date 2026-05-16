#!/usr/bin/env python3
"""Free Fire API Gateway – Token & data fetching with retries."""

import requests
import time
from typing import Optional, Dict
from logs_handler import log_event
import logging

logger = logging.getLogger("FFGateway")

class FreeFireGateway:
    def __init__(self, config: dict):
        self.base_url = config.get("api_base_url", "https://api.dazelpro.com/ff")
        self.default_region = config.get("default_region", "id")
    
    def get_player_stats(self, user_id: str, region: str = None) -> Optional[Dict]:
        """Fetch Free Fire player statistics (mock example using public API)."""
        region = region or self.default_region
        url = f"{self.base_url}/player/{user_id}?region={region}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            log_event(logger, f"🎮 FF stats fetched for {user_id}")
            return data
        except Exception as e:
            log_event(logger, f"❌ FF API error: {e}", level="error")
            return None
    
    def get_active_tokens(self) -> list:
        """Simulate fetching active session tokens."""
        # In real implementation, this would query a DB or external endpoint
        return ["ff_demo_token_xyz"]