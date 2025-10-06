"""
Test utilities for ThinkingSDK E2E testing
"""
import os
import time
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class ThinkingSDKTestHelper:
    """Helper class for ThinkingSDK testing"""

    def __init__(self):
        self.server_url = os.getenv('THINKING_SDK_SERVER_URL', 'http://localhost:8000')
        self.api_key = os.getenv('THINKINGSDK_API_KEY')

    def wait_for_exception_processing(self, timeout: int = 10) -> bool:
        """Wait for exception to be processed by server"""
        print(f"Waiting {timeout}s for exception processing...")
        time.sleep(timeout)
        return True

    def get_latest_exceptions(self, limit: int = 10) -> list:
        """Fetch latest exceptions from server"""
        response = requests.get(
            f"{self.server_url}/api/fix-attempts",
            headers={'X-THINKINGSDK-KEY': self.api_key},
            params={'limit': limit}
        )
        if response.ok:
            return response.json().get('exceptions', [])
        return []

    def check_exception_grouped(self, error_type: str, error_message: str) -> bool:
        """Check if an exception was properly grouped"""
        exceptions = self.get_latest_exceptions()
        for exc in exceptions:
            if exc['error_type'] == error_type and error_message in exc['error_message']:
                print(f"✓ Exception grouped: {error_type}: {error_message}")
                return True
        print(f"✗ Exception not found: {error_type}: {error_message}")
        return False

    def get_exception_count(self, error_type: str) -> int:
        """Get occurrence count for a specific exception type"""
        exceptions = self.get_latest_exceptions()
        for exc in exceptions:
            if exc['error_type'] == error_type:
                return exc.get('occurrence_count', 0)
        return 0

    def cleanup_test_data(self):
        """Cleanup after test (if needed)"""
        # In real scenario, we might want to mark test exceptions
        # For now, we'll just pass
        pass

    def setup_test_environment(self):
        """Setup test environment"""
        if not self.api_key:
            raise ValueError("THINKINGSDK_API_KEY not set in .env file")

        # Verify server is accessible
        try:
            response = requests.get(f"{self.server_url}/health")
            if response.ok:
                print(f"✓ Server accessible at {self.server_url}")
            else:
                print(f"✗ Server returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to server at {self.server_url}")
            raise

    def create_test_context(self, test_name: str) -> Dict[str, Any]:
        """Create context for test execution"""
        return {
            'test_name': test_name,
            'timestamp': time.time(),
            'api_key': self.api_key,
            'server_url': self.server_url
        }


class MultiOrgTestHelper(ThinkingSDKTestHelper):
    """Helper for multi-organization testing"""

    def __init__(self):
        super().__init__()
        # Support multiple API keys for different orgs
        self.org1_key = os.getenv('THINKINGSDK_API_KEY_ORG1', self.api_key)
        self.org2_key = os.getenv('THINKINGSDK_API_KEY_ORG2')

    def setup_multi_org(self) -> Dict[str, str]:
        """Setup multiple organizations for testing"""
        orgs = {'org1': self.org1_key}

        if self.org2_key:
            orgs['org2'] = self.org2_key
            print("✓ Multi-org testing enabled")
        else:
            print("ℹ Single org testing (set THINKINGSDK_API_KEY_ORG2 for multi-org)")

        return orgs