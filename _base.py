diff --git a/database_issues/database_pool_exhaustion_scenario.py b/database_issues/database_pool_exhaustion_scenario.py
index 298c94e..60a2039 100644
--- a/database_issues/database_pool_exhaustion_scenario.py
+++ b/database_issues/database_pool_exhaustion_scenario.py
@@ -18,20 +18,28 @@ connection_pool = []
 pool_lock = threading.Lock()
 active_connections = 0
 
-def get_connection():
-    """Process getting connection from pool"""
+def get_connection(timeout=10.0):
+    """Process getting connection from pool with timeout and retry logic"""
     global active_connections
-    
-    with pool_lock:
-        if active_connections >= MAX_CONNECTIONS:
-            # Pool exhausted - this should be detected by ThinkingSDK
-            raise RuntimeError(f"Connection pool exhausted! Active: {active_connections}, Max: {MAX_CONNECTIONS}")
-        
-        active_connections += 1
-        conn = sqlite3.connect(":memory:", check_same_thread=False)
-        connection_pool.append(conn)
-        
-        return conn
+
+    start_time = time.time()
+    retry_count = 0
+
+    while time.time() - start_time < timeout:
+        with pool_lock:
+            if active_connections < MAX_CONNECTIONS:
+                active_connections += 1
+                conn = sqlite3.connect(":memory:", check_same_thread=False)
+                connection_pool.append(conn)
+                return conn
+
+        # Pool is full, wait and retry
+        retry_count += 1
+        wait_time = min(0.1 * retry_count, 1.0)  # Exponential backoff up to 1 second
+        time.sleep(wait_time)
+
+    # Timeout exceeded - this should be detected by ThinkingSDK
+    raise RuntimeError(f"Connection pool exhausted! Active: {active_connections}, Max: {MAX_CONNECTIONS}, Timeout after {timeout}s")
 
 def release_connection(conn):
     """Release connection back to pool"""
@@ -48,8 +56,10 @@ def database_worker(worker_id, hold_time=2.0):
     try:
         
         
-        # Get connection from pool
-        conn = get_connection()
+        # Get connection from pool with timeout
+        # Use shorter timeout for testing to still demonstrate pool exhaustion
+        timeout = 1.0 if worker_id >= 6 else 5.0
+        conn = get_connection(timeout=timeout)
         
         # Process database work
         cursor = conn.cursor()
@@ -77,8 +87,8 @@ def database_worker(worker_id, hold_time=2.0):
 def process_n_plus_one_queries():
     """Process N+1 query problem"""
     try:
-        
-        conn = get_connection()
+
+        conn = get_connection(timeout=3.0)
         cursor = conn.cursor()
         
         # Create tables
@@ -141,11 +151,13 @@ def process_n_plus_one_queries():
             release_connection(conn)
 
 def main():
-    
+    print("Starting database pool exhaustion scenario...")
+
     try:
         # Test 1: Pool exhaustion with concurrent workers
-        
-        
+        print(f"Test 1: Pool exhaustion - MAX_CONNECTIONS={MAX_CONNECTIONS}")
+        print(f"Initial active connections: {active_connections}")
+
         futures = []
         with ThreadPoolExecutor(max_workers=10) as executor:
             # Submit more workers than available connections
@@ -162,32 +174,36 @@ def main():
             for future in as_completed(futures, timeout=15):
                 try:
                     result = future.result()
+                    print(f"Completed: {result}")
                     completed_count += 1
                 except Exception as e:
+                    print(f"Worker failed: {type(e).__name__}: {e}")
                     error_count += 1
         
-        
+        print(f"Test 1 results: {completed_count} completed, {error_count} errors")
+
         # Test 2: N+1 Query Problem
-        
+        print("\nTest 2: N+1 Query Problem")
         author_books = process_n_plus_one_queries()
-        
-        
+        print(f"Processed {len(author_books)} authors with their books")
+
         # Test 3: Connection leak processing
+        print("\nTest 3: Connection leak scenario")
         
         
         leaked_connections = []
         try:
             # Intentionally "leak" connections (get but don't release)
             for i in range(3):
-                conn = get_connection()
+                conn = get_connection(timeout=2.0)
                 leaked_connections.append(conn)
                 
             
             # Try to get more connections - should fail
-            extra_conn = get_connection()
+            extra_conn = get_connection(timeout=2.0)
             
         except RuntimeError as e:
-            
+            print(f"Expected pool exhaustion: {e}")
         finally:
             # Clean up leaked connections
             for i, conn in enumerate(leaked_connections):
@@ -209,6 +225,7 @@ if __name__ == "__main__":
     try:
         main()
     except Exception as e:
+        print(f"Main execution error: {e}")
     finally:
         
         thinking.stop()
\ No newline at end of file
