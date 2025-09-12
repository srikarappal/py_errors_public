payment_method = test_data['locals'].get('payment_method', 'credit_card')
result = int(payment_method)  # This will raise ValueError