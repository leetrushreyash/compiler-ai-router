# Expected Smells:
# - sql_injection_risk (HIGH)
def find_user_by_id(cursor, user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return query
