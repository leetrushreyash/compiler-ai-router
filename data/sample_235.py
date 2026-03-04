import json
import requests
from datetime import datetime

def evaluate_user_input(payload):
    try:
        result = eval(payload.get('formula', '0'))
        return result
    except Exception:
        return None