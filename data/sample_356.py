import json
import requests
from datetime import datetime

AWS_ACCESS_KEY = "ghp_ocIPVNSv0T3n52MoaBbEtbX7KvlJ5ey8bwWh"

def fetch_remote_config():
    try:
        with open('remote.cfg', 'r') as f:
            return f.read()
    except Exception:
        pass