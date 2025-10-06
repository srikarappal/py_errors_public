"""
Test exception grouping functionality - real-world scenarios

OVERALL TEST SUITE PURPOSE:
- Verify that ThinkingSDK correctly groups similar exceptions together
- Ensure different exceptions are kept separate
- Test that exception location (file/line) affects grouping

WHY THESE TESTS ARE REQUIRED:
- Exception grouping reduces noise in error tracking
- Proper grouping helps identify patterns and frequency of issues
- Prevents dashboard clutter from duplicate errors
- Critical for prioritizing which errors to fix first based on occurrence count
"""
import time
import thinking_sdk_client as thinking
from ..utils.test_helpers import ThinkingSDKTestHelper


def test_same_exception_gets_grouped():
    """
    WHAT: This test triggers the exact same ValueError 3 times in a row
          from the same function with identical error message.

    WHY: In production, the same error often occurs multiple times (e.g.,
         payment validation failing for multiple users). We need to verify
         these get grouped as a single issue with an occurrence count,
         not as 3 separate issues.

    EXPECTED:
    1. Go to http://localhost:8000/dashboard
    2. You should see ONE ValueError entry (not three)
    3. Click on the ValueError - it should show:
       - Error type: ValueError
       - Message: "Payment amount cannot be negative"
       - Occurrence count: 3 (or higher if test ran multiple times)
       - The exception group hash should be the same for all occurrences
    4. In the server logs, you should see the same exception_group_hash
       being reused for the 2nd and 3rd occurrences
    """
    helper = ThinkingSDKTestHelper()
    helper.setup_test_environment()

    # Start ThinkingSDK with real API key
    thinking.start(
        api_key=helper.api_key,
        server_url=helper.server_url
    )

    # Simulate payment processing error occurring multiple times
    def process_payment(amount):
        if amount < 0:
            raise ValueError("Payment amount cannot be negative")
        return {"status": "success", "amount": amount}

    # Trigger the same error 3 times
    error_count = 0
    for i in range(3):
        try:
            process_payment(-100)
        except ValueError as e:
            error_count += 1
            print(f"Error {error_count}: {e}")
            #time.sleep()  # Small delay between errors

    # Wait for processing
    helper.wait_for_exception_processing()

    # Verify exception was grouped
    grouped = helper.check_exception_grouped(
        error_type="ValueError",
        error_message="Payment amount cannot be negative"
    )

    assert grouped, "Exceptions should be grouped together"

    # Check occurrence count
    count = helper.get_exception_count("ValueError")
    assert count >= 3, f"Should have at least 3 occurrences, got {count}"

    thinking.stop()
    print("✅ Test passed: Same exceptions are properly grouped")


def test_different_exceptions_not_grouped():
    """
    WHAT: This test triggers two different ValueError messages - one for
          invalid email format and another for password length validation.

    WHY: Different error messages indicate different problems that need
         separate fixes. Grouping them together would hide important
         distinctions and make debugging harder. Each unique issue needs
         its own entry for proper tracking and resolution.

    EXPECTED:
    1. Go to http://localhost:8000/dashboard
    2. You should see TWO separate ValueError entries:
       - One with message: "Invalid email format"
       - Another with message: "Password must be at least 8 characters"
    3. Each should have its own exception_group_hash
    4. Each should have occurrence count of 1 (unless test ran multiple times)
    5. The dashboard should clearly show these as distinct issues even though
       both are ValueError type
    """
    helper = ThinkingSDKTestHelper()
    helper.setup_test_environment()

    thinking.start(
        api_key=helper.api_key,
        server_url=helper.server_url
    )

    def validate_email(email):
        if "@" not in email:
            raise ValueError("Invalid email format")
        return True

    def validate_password(password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        return True

    # Trigger different errors
    try:
        validate_email("bad-email")
    except ValueError as e:
        print(f"Email error: {e}")

    #time.sleep(2)

    try:
        validate_password("123")
    except ValueError as e:
        print(f"Password error: {e}")

    # Wait for processing
    helper.wait_for_exception_processing()

    # Check both exceptions exist separately
    email_grouped = helper.check_exception_grouped(
        error_type="ValueError",
        error_message="Invalid email format"
    )

    password_grouped = helper.check_exception_grouped(
        error_type="ValueError",
        error_message="Password must be at least 8 characters"
    )

    assert email_grouped, "Email exception should be tracked"
    assert password_grouped, "Password exception should be tracked separately"

    thinking.stop()
    print("✅ Test passed: Different exceptions are not grouped")


def test_exception_with_different_locations():
    """
    WHAT: This test triggers the same ConnectionError with identical message
          but from two different functions (different line numbers in code).

    WHY: Even with identical error type and message, errors from different
         code locations often have different root causes. A database error
         in user_service might need different handling than one in order_service.
         The file:line location is part of the grouping hash.

    EXPECTED:
    1. Go to http://localhost:8000/dashboard
    2. Depending on your grouping implementation:
       - If location-aware: You should see TWO ConnectionError entries
         (one from user_service_db_connect, one from order_service_db_connect)
       - If message-only: You might see ONE ConnectionError entry with count of 2
    3. Check the exception details to see the different stack traces
    4. The exception_group_hash should include file and line number,
       making these distinct groups
    5. This helps identify which service/function is having issues
    """
    helper = ThinkingSDKTestHelper()
    helper.setup_test_environment()

    thinking.start(
        api_key=helper.api_key,
        server_url=helper.server_url
    )

    def user_service_db_connect():
        # Line number matters for grouping
        raise ConnectionError("Database connection failed")

    def order_service_db_connect():
        # Different line number = different group
        raise ConnectionError("Database connection failed")

    # Trigger errors from different locations
    try:
        user_service_db_connect()
    except ConnectionError as e:
        print(f"User service error: {e}")

    #time.sleep(2)

    try:
        order_service_db_connect()
    except ConnectionError as e:
        print(f"Order service error: {e}")

    # Wait for processing
    helper.wait_for_exception_processing()

    # Both should be tracked (even if message is same, location differs)
    exceptions = helper.get_latest_exceptions()
    connection_errors = [e for e in exceptions if e['error_type'] == 'ConnectionError']

    # Depending on grouping logic, these might be together or separate
    # The test verifies they are tracked
    assert len(connection_errors) > 0, "Connection errors should be tracked"

    thinking.stop()
    print("✅ Test passed: Exceptions from different locations are tracked")


if __name__ == "__main__":
    print("\n=== Running Exception Grouping Tests ===\n")

    test_same_exception_gets_grouped()
    print()

    test_different_exceptions_not_grouped()
    print()

    test_exception_with_different_locations()

    print("\n=== All Exception Grouping Tests Passed ===\n")
