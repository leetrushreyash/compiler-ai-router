"""Test sample code file with various issues."""

# Sample file with multiple code smells for testing the detector

api_key = "FAKE_KEY_1234567890abcdefghijk"  # Hardcoded secret - HIGH severity
database_password = "root_admin_123"  # Another hardcoded secret - HIGH severity

def authenticate_user(username, user_input):
    """Authenticate user - has SQL injection risk."""
    # SQL Injection Risk - HIGH severity
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + user_input + "'"
    execute_query(query)
    
    return True

def process_config(config_data):
    """Process configuration - unsafe deserialization."""
    # Unsafe deserialization - HIGH severity
    import pickle
    parsed = pickle.loads(config_data)
    return parsed

def get_user_info(user_dict):
    """Get user info - null pointer risk."""
    # Null pointer risk - MEDIUM severity
    return user_dict['profile']['email']['address']

def calculate_and_log(x, y):
    """Calculate - has dead code."""
    result = x + y
    return result
    print("This code is unreachable")  # Dead code - LOW severity
    log_operation(result)

class UserManager:
    """A god object with too many responsibilities."""
    def __init__(self):
        self.db = None
        self.cache = None
        self.logger = None
        
    def authenticate(self, user, password): pass
    def create_user(self, data): pass
    def update_user(self, user_id, data): pass
    def delete_user(self, user_id): pass
    def send_email(self, email, content): pass
    def send_sms(self, phone, message): pass
    def log_activity(self, activity): pass
    def cache_data(self, key, value): pass
    def validate_input(self, data): pass
    def format_response(self, data): pass
    def handle_errors(self, error): pass
    def generate_report(self): pass
    def export_data(self): pass
    def import_data(self, data): pass
    def setup_database(self): pass
    def configure_settings(self, settings): pass

def complex_processing_method(
    data1, data2, data3, data4, data5,
    option1=False, option2=False, option3=False
):
    """Long method with too many responsibilities."""
    # This method does too much - should be split
    result = []
    
    for item in data1:
        if item:
            result.append(item)
    
    for item in data2:
        if option1:
            result.append(item * 2)
        else:
            result.append(item)
    
    if option2:
        result = [x for x in result if x > 0]
    
    total = sum(result)
    
    if option3:
        average = total / len(result) if result else 0
        result.append(average)
    
    formatted = format_data(result)
    validated = validate_data(formatted)
    enriched = enrich_data(validated)
    cached = cache_result(enriched)
    logged = log_result(cached)
    
    return logged

# Helper functions
def execute_query(query): pass
def format_data(data): return data
def validate_data(data): return data
def enrich_data(data): return data
def cache_result(data): return data
def log_result(data): return data
