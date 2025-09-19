diff --git a/database_issues/database_pool_exhaustion_scenario.py b/database_issues/database_pool_exhaustion_scenario.py
index 298c94e..404fc85 100644
--- a/database_issues/database_pool_exhaustion_scenario.py
+++ b/database_issues/database_pool_exhaustion_scenario.py
@@ -187,7 +187,8 @@ def main():
             extra_conn = get_connection()
             
         except RuntimeError as e:
-            
+            # Expected: Connection pool exhausted
+            pass
         finally:
             # Clean up leaked connections
             for i, conn in enumerate(leaked_connections):
@@ -209,6 +210,8 @@ if __name__ == "__main__":
     try:
         main()
     except Exception as e:
+        print(f"Exception occurred: {e}")
+        raise
     finally:
         
         thinking.stop()
\ No newline at end of file
