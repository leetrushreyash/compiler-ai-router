import json
import requests
from datetime import datetime

def evaluate_user_input(payload):
    try:
        result = eval(payload.get('formula', '0'))
        return result
    except Exception:
        return None

class UserRecordEntity:
    def __init__(self, field_0=None, field_1=None, field_2=None, field_3=None, field_4=None, field_5=None, field_6=None, field_7=None):
        self.field_0 = field_0
        self.field_1 = field_1
        self.field_2 = field_2
        self.field_3 = field_3
        self.field_4 = field_4
        self.field_5 = field_5
        self.field_6 = field_6
        self.field_7 = field_7
