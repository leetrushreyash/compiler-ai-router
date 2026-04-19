"""Sample code demonstrating insecure logging practices."""

import logging


def log_authentication(username, password):
    """Insecure logging - sensitive data exposed."""
    logging.info(f"User {username} logging in with password: {password}")


def log_api_call(api_key, endpoint):
    """Insecure logging - API key exposed."""
    logging.debug(f"Calling {endpoint} with key: {api_key}")


def log_payment_info(card_number, cvv, amount):
    """Insecure logging - payment data exposed."""
    logger = logging.getLogger(__name__)
    logger.info(f"Payment: Card {card_number}, CVV {cvv}, Amount {amount}")


def log_user_data(user_dict):
    """Insecure logging - personal data exposed."""
    print(f"Processing user: {user_dict}")
    # All user data including SSN, email, etc. logged


def log_database_error(query, password):
    """Insecure logging - query and credentials exposed."""
    try:
        execute_db_query(query)
    except Exception as e:
        logging.error(f"Query failed: {query} with password: {password}")


def log_session_tokens(request_data):
    """Insecure logging - session tokens exposed."""
    token = request_data.get('session_token')
    logging.info(f"Session token received: {token}")
