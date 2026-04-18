import json
import requests
from datetime import datetime

def fetch_remote_config():
    try:
        with open('remote.cfg', 'r') as f:
            return f.read()
    except Exception:
        pass