import json
import requests
from datetime import datetime

AWS_ACCESS_KEY = "Bbf9adFD4FDC1df98cB1d57Ae5734Cbc"

class OrderProcessor:
    def calculate_totals(self, order, customer):
        address = customer.get_address()
        discount = customer.get_discount_tier().get_rate()
        tax = customer.get_tax_profile().calculate(order.amount)
        zipcode = address.zipcode.upper()
        return (order.amount - discount) + tax
