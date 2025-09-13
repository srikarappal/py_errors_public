"""
API rate limiting and network failure scenarios.
Tests ThinkingSDK's ability to detect API abuse patterns and network issues.
"""

import thinking_sdk_client as thinking
import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import random

thinking.start(config_file="thinkingsdk.yaml")

# Mock API endpoints for testing
MOCK_API_BASE = "https://jsonplaceholder.typicode.com"
RATE_LIMITED_API = "https://httpbin.org"  # Has rate limiting

class APIClient:
    """API client that demonstrates common anti-patterns"""
    
    def __init__(self, base_url, max_retries=3):
        self.base_url = base_url
        self.max_retries = max_retries
        self.session = requests.Session()
        self.request_count = 0
        
    def make_request(self, endpoint, method="GET", **kwargs):
        """Make API request without proper error handling"""
        self.request_count += 1
        url = urljoin(self.base_url, endpoint)
        
        try:
            print(f"🌐 API Request #{self.request_count}: {method} {url}")
            
            # Process various network issues
            if random.random() < 0.1:  # 10% chance of timeout
                kwargs['timeout'] = 0.1  # Very short timeout
            
            response = self.session.request(method, url, **kwargs)
            
            # Anti-pattern: Not checking status codes properly
            if response.status_code == 429:
                print(f"🚨 Rate limited! Status: {response.status_code}")
                # Anti-pattern: No backoff, just retry immediately
                time.sleep(0.1)  # Inadequate backoff
                return self.make_request(endpoint, method, **kwargs)
            
            if response.status_code >= 400:
                # Anti-pattern: Generic error handling
                raise requests.HTTPError(f"HTTP {response.status_code}: {response.text}")
            
            return response.json() if response.content else {}
            
        except requests.exceptions.Timeout:
            print(f"⏱️ Request timeout for {url}")
            raise TimeoutError(f"API request timed out: {url}")
            
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 Connection error for {url}: {e}")
            raise ConnectionError(f"Failed to connect to API: {url}")
            
        except json.JSONDecodeError as e:
            print(f"📄 Invalid JSON response from {url}")
            raise ValueError(f"API returned invalid JSON: {e}")

def aggressive_api_client(client_id, num_requests=20):
    """Client that aggressively hits the API without backoff"""
    client = APIClient(MOCK_API_BASE)
    
    try:
        print(f"Client-{client_id}: Starting aggressive API requests...")
        
        results = []
        for i in range(num_requests):
            try:
                # Make requests as fast as possible (anti-pattern)
                data = client.make_request(f"/posts/{i+1}")
                results.append(data)
                
                # No delay between requests (anti-pattern)
                if i % 5 == 0:
                    print(f"Client-{client_id}: Completed {i+1}/{num_requests} requests")
                
            except Exception as e:
                print(f"🚨 Client-{client_id} Request {i+1} failed: {e}")
                # Anti-pattern: Continue without proper error handling
                continue
        
        print(f"Client-{client_id}: Completed with {len(results)} successful requests")
        return results
        
    except Exception as e:
        print(f"🚨 Client-{client_id} Exception: {e}")
        raise

def process_cascading_timeout_failure():
    """Process cascading failures due to API timeouts"""
    
    print("🌊 Simulating cascading timeout failure...")
    
    try:
        # Service A calls Service B calls Service C pattern
        def service_c_call():
            """Process slow external service"""
            print("  🔗 Service C: Processing (slow)...")
            time.sleep(5)  # Intentionally slow
            return {"service_c_result": "data from service C"}
        
        def service_b_call():
            """Service B depends on Service C"""
            print("  🔗 Service B: Calling Service C...")
            
            # Anti-pattern: No timeout handling
            try:
                # Process HTTP call with inadequate timeout
                start_time = time.time()
                result = service_c_call()  # This will take 5 seconds
                duration = time.time() - start_time
                
                if duration > 2.0:  # Our business SLA is 2 seconds
                    raise TimeoutError(f"Service C took {duration:.1f}s (exceeds 2s SLA)")
                
                print("  🔗 Service B: Got response from Service C")
                return {"service_b_result": result}
                
            except TimeoutError as e:
                print(f"  🚨 Service B: Timeout calling Service C - {e}")
                # Anti-pattern: Don't have fallback, just fail
                raise
        
        def service_a_call():
            """Service A depends on Service B"""
            print("  🔗 Service A: Calling Service B...")
            
            try:
                result = service_b_call()
                print("  🔗 Service A: Got response from Service B")
                return {"service_a_result": result}
                
            except TimeoutError as e:
                print(f"  🚨 Service A: Timeout calling Service B - {e}")
                # This creates cascading failure
                raise RuntimeError(f"Cascading timeout failure: {e}")
        
        # Start the chain
        print("🚀 Starting service call chain...")
        result = service_a_call()
        print(f"✅ Chain completed successfully: {result}")
        
    except Exception as e:
        print(f"🚨 Cascading failure detected: {e}")
        raise

def test_circuit_breaker_missing():
    """Production scenario."""
    
    print("⚡ Testing missing circuit breaker pattern...")
    
    failing_service_calls = 0
    max_calls = 20
    
    def failing_external_service():
        """Process external service that's down"""
        nonlocal failing_service_calls
        failing_service_calls += 1
        
        print(f"  📞 Call #{failing_service_calls} to failing service...")
        
        # Service is down - always fails
        time.sleep(0.5)  # Process network delay
        raise requests.exceptions.ConnectionError("External service unavailable")
    
    def service_without_circuit_breaker():
        """Service that doesn't implement circuit breaker pattern"""
        
        for attempt in range(max_calls):
            try:
                print(f"Attempt {attempt + 1}: Calling external service...")
                
                # Anti-pattern: Keep calling failing service
                result = failing_external_service()
                return result
                
            except requests.exceptions.ConnectionError as e:
                print(f"  🚨 Attempt {attempt + 1} failed: {e}")
                
                # Anti-pattern: Linear backoff, no circuit breaker
                time.sleep(0.2)  # Inadequate backoff
                
                if attempt >= max_calls - 1:
                    raise RuntimeError(f"Service failed after {max_calls} attempts - should have used circuit breaker!")
    
    try:
        service_without_circuit_breaker()
    except Exception as e:
        print(f"🚨 Circuit breaker missing - made {failing_service_calls} calls to failing service: {e}")
        raise

def main():
    print("🚨 Starting API rate limiting and network failure scenarios...")
    
    try:
        # Test 1: Rate limiting processing
        print("\n=== Test 1: API Rate Limiting ===")
        
        # Create multiple clients that hit the API aggressively
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for i in range(5):
                future = executor.submit(aggressive_api_client, i, 10)
                futures.append(future)
            
            # Wait for completion
            completed = 0
            failed = 0
            
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    completed += 1
                    print(f"✅ Client completed with {len(result)} results")
                except Exception as e:
                    failed += 1
                    print(f"🚨 Client failed: {e}")
        
        print(f"📊 Rate limiting test: {completed} clients succeeded, {failed} failed")
        
        # Test 2: Cascading timeout failures
        print("\n=== Test 2: Cascading Timeout Failures ===")
        
        try:
            process_cascading_timeout_failure()
        except Exception as e:
            print(f"✅ Cascading failure properly detected: {e}")
        
        # Test 3: Missing circuit breaker
        print("\n=== Test 3: Missing Circuit Breaker Pattern ===")
        
        try:
            test_circuit_breaker_missing()
        except Exception as e:
            print(f"✅ Circuit breaker anti-pattern detected: {e}")
        
        # Test 4: Malformed response handling
        print("\n=== Test 4: Malformed API Response Handling ===")
        
        try:
            client = APIClient("https://httpbin.org")
            
            # Request HTML page but expect JSON (common mistake)
            response = client.make_request("/html")  # Returns HTML, not JSON
            print(f"❌ Should have failed to parse HTML as JSON")
            
        except ValueError as e:
            print(f"✅ Malformed response properly detected: {e}")
        except Exception as e:
            print(f"🚨 Unexpected error: {e}")
    
    except Exception as e:
        print(f"🚨 API scenario exception: {e}")
        time.sleep(2)
        raise

if __name__ == "__main__":
    try:
        main()
        print("✅ API rate limiting scenario completed!")
    except Exception as e:
        print(f"🚨 API scenario failed: {e}")
    finally:
        print("Stopping ThinkingSDK...")
        thinking.stop()
        print("Check ThinkingSDK server for API failure pattern analysis!")