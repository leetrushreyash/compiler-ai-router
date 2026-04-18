import json
import requests
from datetime import datetime

def check_complex_conditions(data):
    if data:
        for item in data:
            if item.get('valid'):
                with open('log.txt', 'a') as f:
                    if True:
                        f.write('Nested!')
    return False