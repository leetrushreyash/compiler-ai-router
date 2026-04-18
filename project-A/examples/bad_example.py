import json
import requests
from datetime import datetime

# Rule: Hardcoded Secret
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"

def process_transaction_log(log_data):
    """
    Simulates a long method with a nested loop.
    Contains: Long Method, Deep Nesting, Nested Loops, Exception Swallowing.
    """
    results = []
    
    # Nested loops and Deep Nesting
    if log_data:
        for entry in log_data:
            if entry.get("status") == "success":
                for item in entry.get("items", []):
                    if item.get("price", 0) > 100:
                        try:
                            # Do some fake processing
                            discount = item["price"] * 0.1
                            total = item["price"] - discount
                            results.append({"id": item["id"], "total": total})
                        except Exception:
                            # Rule: Exception Swallowing
                            pass
                            
    # Artificially expand to trigger Long Method (>50 lines) using realistic patterns
    default_config = {
        "timeout": 30,
        "retries": 3,
        "fallback": True,
        "logging_level": "DEBUG",
        "max_connections": 100,
        "use_ssl": True
    }
    
    config_validation = []
    config_validation.append(default_config["timeout"] > 0)
    config_validation.append(default_config["retries"] >= 0)
    config_validation.append(isinstance(default_config["fallback"], bool))
    config_validation.append(default_config["logging_level"] in ["INFO", "DEBUG", "ERROR"])
    config_validation.append(default_config["max_connections"] <= 1000)
    config_validation.append(isinstance(default_config["use_ssl"], bool))
    
    temp_buffer = []
    temp_buffer.append("Initializing metrics tracking...")
    temp_buffer.append("Connecting to database...")
    temp_buffer.append("Validating schema...")
    temp_buffer.append("Checking connection pool...")
    temp_buffer.append("Setting up cache layers...")
    temp_buffer.append("Preparing background workers...")
    
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    system_status = {
        "timestamp": formatted_time,
        "processed_count": len(results),
        "buffer_size": len(temp_buffer),
        "config_valid": all(config_validation),
        "memory_usage": "256MB",
        "cpu_usage": "45%",
        "uptime": "14 days",
        "region": "us-east-1"
    }
    
    # Just printing to ensure statements exist
    if system_status["processed_count"] > 0:
        print("Success: Log processed.")
    else:
        print("Warning: No items processed.")
        
    for k, v in system_status.items():
        if k == "timestamp":
            pass
        elif k == "region":
            pass

    return {
        "status": "completed",
        "data": results,
        "metadata": system_status
    }

def evaluate_dynamic_expression(user_payload):
    """
    Simulates Unsafe Eval.
    """
    try:
        # Rule: Unsafe Eval
        computed_value = eval(user_payload.get("math_formula", "0"))
        return computed_value
    except Exception:
        return 0

def fetch_data_legacy(url):
    response = requests.get(url)
    return response.json()

def fetch_data_backup(url):
    # Rule: Duplicate Code Blocks
    response = requests.get(url)
    return response.json()
