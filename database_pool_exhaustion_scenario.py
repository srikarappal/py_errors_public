diff --git a/database_issues/database_pool_exhaustion_scenario.py b/database_issues/database_pool_exhaustion_scenario.py
index 298c94e..3dadda1 100644
--- a/database_issues/database_pool_exhaustion_scenario.py
+++ b/database_issues/database_pool_exhaustion_scenario.py
@@ -18,20 +18,26 @@ connection_pool = []
 pool_lock = threading.Lock()
 active_connections = 0
 
-def get_connection():
-    """Process getting connection from pool"""
+def get_connection(timeout=8.0):
+    """Process getting connection from pool with timeout"""
     global active_connections
-    
+
+    start_time = time.time()
+    while time.time() - start_time < timeout:
+        with pool_lock:
+            if active_connections < MAX_CONNECTIONS:
+                active_connections += 1
+                conn = sqlite3.connect(":memory:", check_same_thread=False)
+                connection_pool.append(conn)
+                return conn
+
+        # Wait briefly before retrying
+        time.sleep(0.1)
+
+    # Timeout exceeded - capture current state for better debugging
     with pool_lock:
-        if active_connections >= MAX_CONNECTIONS:
-            # Pool exhausted - this should be detected by ThinkingSDK
-            raise RuntimeError(f"Connection pool exhausted! Active: {active_connections}, Max: {MAX_CONNECTIONS}")
-        
-        active_connections += 1
-        conn = sqlite3.connect(":memory:", check_same_thread=False)
-        connection_pool.append(conn)
-        
-        return conn
+        current_active = active_connections
+    raise RuntimeError(f"Connection pool exhausted! Active: {current_active}, Max: {MAX_CONNECTIONS}")
 
 def release_connection(conn):
     """Release connection back to pool"""
@@ -150,21 +156,25 @@ def main():
         with ThreadPoolExecutor(max_workers=10) as executor:
             # Submit more workers than available connections
             for i in range(8):  # 8 workers, but only 5 connections available
-                hold_time = 3.0 if i < 6 else 1.0  # First 6 hold longer
+                hold_time = 2.0 if i < 6 else 0.5  # First 6 hold longer, but reduced time
                 future = executor.submit(database_worker, i, hold_time)
                 futures.append(future)
-                time.sleep(0.2)  # Stagger the requests
+                time.sleep(0.1)  # Reduced stagger time
             
             # Wait for completion
             completed_count = 0
             error_count = 0
             
-            for future in as_completed(futures, timeout=15):
+            for future in as_completed(futures, timeout=20):  # Increased timeout
                 try:
                     result = future.result()
                     completed_count += 1
+                    print(f"Completed: {result}")
                 except Exception as e:
                     error_count += 1
+                    print(f"Worker failed: {e}")
+
+            print(f"Pool exhaustion test completed: {completed_count} succeeded, {error_count} failed")
         
         
         # Test 2: N+1 Query Problem
@@ -173,26 +183,32 @@ def main():
         
         
         # Test 3: Connection leak processing
-        
-        
+        print("\nTesting intentional connection leak scenario...")
+
         leaked_connections = []
         try:
             # Intentionally "leak" connections (get but don't release)
-            for i in range(3):
+            for i in range(MAX_CONNECTIONS):  # Use all available connections
                 conn = get_connection()
                 leaked_connections.append(conn)
-                
-            
-            # Try to get more connections - should fail
-            extra_conn = get_connection()
-            
+                print(f"Leaked connection {i+1}/{MAX_CONNECTIONS}")
+
+
+            # Try to get more connections - should fail due to exhaustion
+            print("Attempting to get additional connection beyond pool limit...")
+            extra_conn = get_connection(timeout=2.0)  # Shorter timeout for this test
+
         except RuntimeError as e:
-            
+            # Expected pool exhaustion error - log and continue
+            print(f"Expected pool exhaustion caught: {e}")
         finally:
             # Clean up leaked connections
+            print("Cleaning up leaked connections...")
             for i, conn in enumerate(leaked_connections):
-                
                 release_connection(conn)
+                print(f"Released leaked connection {i+1}")
+
+        print("Connection leak test completed.")
         
     except Exception as e:
         time.sleep(2)  
@@ -209,6 +225,8 @@ if __name__ == "__main__":
     try:
         main()
     except Exception as e:
+        print(f"Error in main: {e}")
+        raise
     finally:
         
         thinking.stop()
\ No newline at end of file
