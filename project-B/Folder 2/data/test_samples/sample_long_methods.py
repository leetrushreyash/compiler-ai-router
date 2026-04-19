"""Sample code demonstrating long method anti-pattern."""

def process_user_registration(username, email, password, phone, address, country, preferences):
    """Very long method doing many things."""
    # Validate username
    if not username or len(username) < 3:
        return {"error": "Username too short"}
    
    if not all(c.isalnum() or c == '_' for c in username):
        return {"error": "Invalid username characters"}
    
    # Validate email
    if not email or '@' not in email:
        return {"error": "Invalid email"}
    
    # Check email already exists
    existing = query_database(f"SELECT * FROM users WHERE email = '{email}'")
    if existing:
        return {"error": "Email already registered"}
    
    # Validate password
    if len(password) < 8:
        return {"error": "Password too short"}
    
    if not any(c.isupper() for c in password):
        return {"error": "Password needs uppercase"}
    
    if not any(c.isdigit() for c in password):
        return {"error": "Password needs digit"}
    
    # Validate phone
    if not phone.replace('-', '').isdigit():
        return {"error": "Invalid phone"}
    
    # Validate address
    if not address:
        return {"error": "Address required"}
    
    # Validate country
    valid_countries = ["US", "UK", "CA", "AU"]
    if country not in valid_countries:
        return {"error": "Invalid country"}
    
    # Process preferences
    pref_list = []
    for pref in preferences:
        if pref in ["newsletter", "sms", "email"]:
            pref_list.append(pref)
    
    # Create user in database
    user_id = create_database_user(username, email, password, phone, address, country)
    
    # Send confirmation email
    send_email(email, "Welcome", f"Welcome {username}")
    
    # Create user profile
    create_user_profile(user_id, preferences=pref_list)
    
    # Update statistics
    increment_user_count()
    
    # Log activity
    log_activity(f"User {username} registered")
    
    # Send welcome SMS if opted in
    if "sms" in pref_list:
        send_sms(phone, "Welcome message")
    
    return {"success": True, "user_id": user_id}
