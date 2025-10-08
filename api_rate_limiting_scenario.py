diff --git a/api_networking/api_rate_limiting_scenario.py b/api_networking/api_rate_limiting_scenario.py
index 83c8016..c801f52 100644
--- a/api_networking/api_rate_limiting_scenario.py
+++ b/api_networking/api_rate_limiting_scenario.py
@@ -49,19 +49,25 @@ class APIClient:
             if response.status_code >= 400:
                 # Anti-pattern: Generic error handling
                 raise requests.HTTPError(f"HTTP {response.status_code}: {response.text}")
-            
-            return response.json() if response.content else {}
+
+            # Check if response has content
+            if not response.content:
+                return {}
+
+            # Attempt to parse JSON
+            try:
+                return response.json()
+            except json.JSONDecodeError as e:
+                # Check content type to provide better error message
+                content_type = response.headers.get('Content-Type', 'unknown')
+                raise ValueError(f"API returned non-JSON content (Content-Type: {content_type}). Expected JSON but got: {response.text[:100]}")
             
         except requests.exceptions.Timeout:
             raise TimeoutError(f"API request timed out: {url}")
             
         except requests.exceptions.ConnectionError as e:
-            
+
             raise ConnectionError(f"Failed to connect to API: {url}")
-            
-        except json.JSONDecodeError as e:
-            
-            raise ValueError(f"API returned invalid JSON: {e}")
 
 def aggressive_api_client(client_id, num_requests=20):
     """Client that aggressively hits the API without backoff"""
@@ -79,8 +85,8 @@ def aggressive_api_client(client_id, num_requests=20):
                 
                 # No delay between requests (anti-pattern)
                 if i % 5 == 0:
-                    
-                
+                    pass  # Anti-pattern: no throttling between request batches
+
             except Exception as e:
                 # Anti-pattern: Continue without proper error handling
                 continue
@@ -221,14 +227,16 @@ def main():
         try:
             process_cascading_timeout_failure()
         except Exception as e:
-        
+            pass  # Expected to fail - testing cascading timeouts
+
         # Test 3: Missing circuit breaker
         
         
         try:
             check_circuit_breaker_missing()
         except Exception as e:
-        
+            pass  # Expected to fail - testing missing circuit breaker
+
         # Test 4: Malformed response handling
         
         
@@ -237,9 +245,11 @@ def main():
             
             # Request HTML page but expect JSON (common mistake)
             response = client.make_request("/html")  # Returns HTML, not JSON
-            
+
         except ValueError as e:
+            pass  # Expected to raise ValueError for non-JSON content
         except Exception as e:
+            pass  # Catch any other unexpected errors
     
     except Exception as e:
         time.sleep(2)
@@ -249,6 +259,6 @@ if __name__ == "__main__":
     try:
         main()
     except Exception as e:
+        pass  # Exceptions already handled and reported
     finally:
-        
         thinking.stop()
\ No newline at end of file
