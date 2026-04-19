"""Sample code demonstrating SQL injection vulnerabilities."""

def search_products(product_name):
    """Vulnerable product search - SQL injection."""
    query = f"SELECT * FROM products WHERE name LIKE '%{product_name}%'"
    return execute_query(query)


def get_user_by_email(email):
    """Vulnerable email lookup - SQL injection."""
    query = "SELECT * FROM users WHERE email = '" + email + "'"
    return execute_query(query)


def filter_by_id(user_id):
    """Vulnerable ID filter - SQL injection."""
    query = f"DELETE FROM users WHERE id = {user_id}"
    execute_query(query)


def search_orders(order_id, customer_id):
    """Multiple injection points."""
    query = f"SELECT * FROM orders WHERE id = {order_id} AND customer = '{customer_id}'"
    return execute_query(query)
