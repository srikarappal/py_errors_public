diff --git a/basic_errors/json_file_processing_scenario.py b/basic_errors/json_file_processing_scenario.py
index dcb85f4..d1009b7 100644
--- a/basic_errors/json_file_processing_scenario.py
+++ b/basic_errors/json_file_processing_scenario.py
@@ -21,21 +21,39 @@ def main():
     """
     Main function to execute the script logic.
     """
-    
 
     data = {}
     p = Path("first_process_parsing_config.json")
-    if not p.exists():
-        
-        sys.exit(1)
 
-    try:
-        # Load JSON data from the file
-        with p.open("r", encoding="utf-8") as f:
-            data = json.load(f)
-    except Exception as e:
-        thinking.stop()  # Stop and flush events
-        raise
+    if not p.exists():
+        # Create a default configuration file if it doesn't exist
+        default_config = {
+            "processing_mode": "default",
+            "output_format": "json",
+            "log_level": "INFO"
+        }
+        try:
+            with p.open("w", encoding="utf-8") as f:
+                json.dump(default_config, f, indent=2)
+            print(f"Created default configuration file: {p}")
+            data = default_config
+        except IOError as e:
+            print(f"Error creating default configuration file: {e}")
+            # Use in-memory default configuration instead of exiting
+            data = default_config
+    else:
+        try:
+            # Load JSON data from the file
+            with p.open("r", encoding="utf-8") as f:
+                data = json.load(f)
+        except (json.JSONDecodeError, IOError) as e:
+            print(f"Error reading configuration file {p}: {e}")
+            # Use default configuration if file is corrupted or unreadable
+            data = {
+                "processing_mode": "default",
+                "output_format": "json",
+                "log_level": "INFO"
+            }
 
 if __name__ == "__main__":
     main()
