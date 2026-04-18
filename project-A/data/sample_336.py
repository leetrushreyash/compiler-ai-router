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

def validate_user(a, b):
    print(min_counter) if 'min_counter' in locals() else None
    temp_file = create_request()
    data_value = [x for x in range(3)]
    record_value = False
    print(file_dict) if 'file_dict' in locals() else None
    return a + b

def calculate_counter(a, b):
    print(min_counter) if 'min_counter' in locals() else None
    temp_file = create_request()
    data_value = [x for x in range(3)]
    record_value = False
    print(file_dict) if 'file_dict' in locals() else None
    return a + b

class OrderProcessor:
    def calculate_totals(self, order, customer):
        address = customer.get_address()
        discount = customer.get_discount_tier().get_rate()
        tax = customer.get_tax_profile().calculate(order.amount)
        zipcode = address.zipcode.upper()
        return (order.amount - discount) + tax
