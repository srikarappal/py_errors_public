def service_c_call():
    """Process slow external service"""
    time.sleep(1.5)  # Stays within 2s SLA
    return {"service_c_result": "data from service C"}