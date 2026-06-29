def sql_injection_check(user_input):
    # Basic SQL injection check function
    # This function checks for common SQL injection patterns in the user input
    sql_injection_patterns = ["'", '"', ";", "--", "/*", "*/", "xp_"]
    
    for pattern in sql_injection_patterns:
        if pattern in user_input:
            raise ValueError("Potential SQL injection detected.")
    
    return user_input