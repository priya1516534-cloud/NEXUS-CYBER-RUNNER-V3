#!/usr/bin/env python3
"""Security Layer – IP whitelisting and Basic Auth for Flask routes."""

import ipaddress
from functools import wraps
from flask import request, Response, jsonify
import json
from global_const import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config_v3.json"
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

ALLOWED_NETS = [ipaddress.ip_network(net) for net in CONFIG["security"]["allowed_ips"]]
BASIC_AUTH_ENABLED = CONFIG["security"]["basic_auth"]["enabled"]
AUTH_USER = CONFIG["security"]["basic_auth"]["username"]
AUTH_PASS = CONFIG["security"]["basic_auth"]["password"]

def ip_whitelist_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = request.remote_addr
        if not any(client_ip in net for net in ALLOWED_NETS):
            return jsonify({"error": "IP not whitelisted"}), 403
        return f(*args, **kwargs)
    return decorated

def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not BASIC_AUTH_ENABLED:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or auth.username != AUTH_USER or auth.password != AUTH_PASS:
            return Response("Authentication required", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated