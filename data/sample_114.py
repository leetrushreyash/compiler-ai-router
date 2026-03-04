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

class OrderProcessor:
    def calculate_totals(self, order, customer):
        address = customer.get_address()
        discount = customer.get_discount_tier().get_rate()
        tax = customer.get_tax_profile().calculate(order.amount)
        zipcode = address.zipcode.upper()
        return (order.amount - discount) + tax
