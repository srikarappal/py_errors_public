#!/usr/bin/env python3
"""
ThinkingSDK E2E Test Runner

This script demonstrates real ThinkingSDK usage by:
1. Starting thinking_sdk_client with real API key
2. Triggering realistic runtime exceptions
3. Letting ThinkingSDK's AI analyze and create GitHub issues/PRs
4. Showing complete end-to-end workflow

Usage:
    python test_runner.py --scenario payment_processing_error
    python test_runner.py --all
    python test_runner.py --category payment_ecommerce
"""

import os
import sys
import time
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import ThinkingSDK Client (the real one!)
try:
    import thinking_sdk_client as thinking
    print("ThinkingSDK Client imported successfully")
except ImportError:
    print("ThinkingSDK Client not found. Run: pip install -r requirements.txt")
    sys.exit(1)

# Import our test scenarios
from mock_github_integration import TestCaseGenerator

class ThinkingSDKTestRunner:
    """Real ThinkingSDK testing using actual client SDK."""

    def __init__(self):
        self.api_key = os.getenv('THINKINGSDK_API_KEY')
        self.server_url = os.getenv('THINKING_SDK_SERVER_URL', 'http://localhost:8000')

        if not self.api_key:
            print("THINKINGSDK_API_KEY not set in .env file")
            print("   Generate an API key from http://localhost:3000/dashboard")
            sys.exit(1)

        print(f"Using API key: {self.api_key[:20]}...")
        print(f"Server URL: {self.server_url}")

    def start_thinking_sdk(self):
        """Start ThinkingSDK client - this is how real users do it!"""
        print("Starting ThinkingSDK client...")

        try:
            thinking.start(
                api_key=self.api_key,
                server_url=self.server_url,
                # Real user configuration using config dict
                config={
                    'instrumentation': {'sample_rate': 1.0},  # Capture everything for testing
                },
                enable_logging=True
            )

            # Add test context after starting
            thinking.add_context("test_environment", "e2e_testing")
            thinking.add_context("user_type", "test_user")
            print("ThinkingSDK started successfully")
            return True

        except Exception as e:
            print(f"Failed to start ThinkingSDK: {e}")
            return False

    def stop_thinking_sdk(self):
        """Stop ThinkingSDK client."""
        print("Stopping ThinkingSDK client...")
        thinking.stop()
        print("ThinkingSDK stopped")

    def _fetch_and_display_insights(self):
        """Fetch and display AI insights from server."""
        try:
            import requests

            # Create session with admin API key
            session_response = requests.post(f"{self.server_url}/auth/session", 
                json={"api_key": self.api_key})
            if not session_response.ok:
                print(f"Failed to create session: {session_response.status_code}")
                return

            session_token = session_response.json()["session_token"]

            # Fetch insights
            insights_response = requests.get(f"{self.server_url}/insights",
                headers={"X-Session-Token": session_token})
            if not insights_response.ok:
                print(f"Failed to fetch insights: {insights_response.status_code}")
                return

            insights = insights_response.json()

            if insights:
                print(f"\nAI ANALYSIS RESULTS ({len(insights)} insights):")
                print("=" * 50)
                for i, insight in enumerate(insights, 1):
                    print(f"\n{i}. INSIGHT_TYPE: {insight.get('insight_type', 'Unknown').upper()} - {insight.get('severity', 'info').upper()}")
                    print(f"   {insight.get('title', 'No title')}")
                    print(f"   {insight.get('body', 'No content')[:200]}...")
                    print(f"   Created: {insight.get('created_at', 'Unknown')}")
                print("=" * 50)
            else:
                print("\nNo AI insights found")

        except Exception as e:
            print(f"Failed to fetch insights: {e}")

    def trigger_test_scenario(self, scenario_name: str):
        """Trigger a specific test scenario with real runtime exception."""
        print(f"Running scenario: {scenario_name}")

        # Get the test case data
        test_generator = TestCaseGenerator()

        scenario_methods = {
            'payment_processing_error': test_generator.generate_payment_processing_error,
            'payment_timeout_error': test_generator.generate_payment_timeout_error,
            'database_keyerror': test_generator.generate_database_keyerror,
            'auth_attributeerror': test_generator.generate_auth_attributeerror,
            'api_indexerror': test_generator.generate_api_indexerror,
            'connection_pool_exhaustion': test_generator.generate_connection_pool_exhaustion,
            'memory_leak_error': test_generator.generate_memory_leak_error,
            'rate_limit_exceeded': test_generator.generate_rate_limit_exceeded_error
        }

        if scenario_name not in scenario_methods:
            print(f"Unknown scenario: {scenario_name}")
            print(f"   Available: {', '.join(scenario_methods.keys())}")
            return False

        try:
            # This is the key difference: we simulate the actual runtime exception
            # that would trigger ThinkingSDK in a real application
            self._simulate_runtime_exception(scenario_name, scenario_methods[scenario_name]())
            return True

        except Exception as e:
            print(f"Scenario execution failed: {e}")
            return False

    def _simulate_runtime_exception(self, scenario_name: str, test_data: Dict[str, Any]):
        """
        Simulate the actual runtime exception that would trigger ThinkingSDK.

        This creates a real Python exception with the context from our test data,
        allowing ThinkingSDK to capture it naturally like it would in production.
        """
        print(f"Simulating {test_data['exception']['type']} exception...")

        # Add test context to ThinkingSDK
        thinking.add_context("test_scenario", scenario_name)
        thinking.add_context("business_impact", test_data.get('business_impact'))
        thinking.add_context("severity", test_data.get('severity'))

        # Create the actual exception type and raise it
        exception_type = test_data['exception']['type']
        exception_message = test_data['exception']['message']

        try:
            if exception_type == 'ValueError':
                # Simulate the actual error condition
                payment_method = test_data['locals'].get('payment_method', 'credit_card')
                result = int(payment_method)  # This will raise ValueError

            elif exception_type == 'KeyError':
                # Simulate database connection pool error
                db_pool = test_data['locals'].get('db_pool', {})
                conn = db_pool['connection']  # This will raise KeyError

            elif exception_type == 'AttributeError':
                # Simulate auth error
                request_user = None
                is_auth = request_user.is_authenticated  # This will raise AttributeError

            elif exception_type == 'IndexError':
                # Simulate API response error
                response_data = test_data['locals'].get('response', {"data": {"results": []}})
                value = response_data['data']['results'][0]['value']  # This will raise IndexError

            else:
                # Generic exception for other types
                raise Exception(f"Simulated {exception_type}: {exception_message}")

        except Exception as e:
            print(f"Exception captured by ThinkingSDK: {type(e).__name__}: {e}")
            print("Waiting for AI analysis...")

            # Give ThinkingSDK time to process and send to server
            time.sleep(0.5)

            # Fetch AI insights from server
            #self._fetch_and_display_insights()

    def run_scenario_with_timing(self, scenario_name: str):
        """Run scenario with performance timing."""
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"TESTING SCENARIO: {scenario_name.upper()}")
        print(f"{'='*60}")

        success = self.trigger_test_scenario(scenario_name)

        elapsed = time.time() - start_time
        print(f"\nTest completed in {elapsed:.2f} seconds")

        if success:
            print("Scenario executed successfully")
            print("Check ThinkingSDK server logs for AI analysis")
            print("Check GitHub for created issues/PRs")
        else:
            print("Scenario failed")

        print(f"{'='*60}\n")
        return success

def main():
    parser = argparse.ArgumentParser(description='ThinkingSDK E2E Test Runner')
    parser.add_argument('--scenario', help='Run specific scenario')
    parser.add_argument('--all', action='store_true', help='Run all scenarios')
    parser.add_argument('--category', help='Run all scenarios in category')
    parser.add_argument('--list', action='store_true', help='List available scenarios')

    args = parser.parse_args()

    runner = ThinkingSDKTestRunner()

    # List scenarios
    if args.list:
        print("Available test scenarios:")
        scenarios = [
            'payment_processing_error', 'payment_timeout_error', 'database_keyerror',
            'auth_attributeerror', 'api_indexerror', 'connection_pool_exhaustion',
            'memory_leak_error', 'rate_limit_exceeded'
        ]
        for scenario in scenarios:
            print(f"  - {scenario}")
        return

    # Start ThinkingSDK
    if not runner.start_thinking_sdk():
        return

    try:
        if args.all:
            print("Running all test scenarios...")
            scenarios = [
                'payment_processing_error', 'database_keyerror', 
                'auth_attributeerror', 'api_indexerror'
            ]

            for scenario in scenarios:
                success = runner.run_scenario_with_timing(scenario)
                if not success:
                    print(f"Scenario {scenario} failed, continuing...")
                time.sleep(2)  # Brief pause between scenarios

        elif args.scenario:
            runner.run_scenario_with_timing(args.scenario)

        else:
            print("Use --scenario <name>, --all, or --list")

    finally:
        # Always stop ThinkingSDK
        runner.stop_thinking_sdk()

if __name__ == "__main__":
    main()
