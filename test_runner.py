if exception_type == 'ValueError':
    # Simulate the actual error condition more robustly
    payment_method = test_data['locals'].get('payment_method', 'credit_card')
    
    # Handle different types of ValueError scenarios
    if isinstance(payment_method, str) and not payment_method.isdigit():
        # This simulates trying to convert a non-numeric string to int
        result = int(payment_method)  # This will raise ValueError with the expected message
    else:
        # Fallback for when payment_method might already be numeric
        # Simulate a different common ValueError scenario
        amount = test_data['locals'].get('amount', 'invalid_amount')
        if isinstance(amount, str) and not str(amount).replace('.', '').replace('-', '').isdigit():
            result = int(amount)  # This will raise ValueError
        else:
            # Final fallback - simulate the exact error from test data
            raise ValueError("invalid literal for int() with base 10: 'credit_card'")