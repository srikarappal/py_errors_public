diff --git a/basic_errors/first_scenario_parsing_config.json b/basic_errors/first_scenario_parsing_config.json
index fe0bcc0..5da1c7e 100644
--- a/basic_errors/first_scenario_parsing_config.json
+++ b/basic_errors/first_scenario_parsing_config.json
@@ -1,6 +1,6 @@
 {
     "name": "MyApp",
-    "features": ["a", "b",],  // trailing comma
-    "retries": 3, // can change 
-  }
+    "features": ["a", "b"],
+    "retries": 3
+}
   
\ No newline at end of file
diff --git a/basic_errors/json_file_processing_scenario.py b/basic_errors/json_file_processing_scenario.py
index dcb85f4..eb8134c 100644
--- a/basic_errors/json_file_processing_scenario.py
+++ b/basic_errors/json_file_processing_scenario.py
@@ -24,18 +24,23 @@ def main():
     
 
     data = {}
-    p = Path("first_process_parsing_config.json")
+    p = Path("basic_errors/first_scenario_parsing_config.json")
     if not p.exists():
-        
+        print(f"Error: Configuration file '{p}' not found.")
         sys.exit(1)
 
     try:
         # Load JSON data from the file
         with p.open("r", encoding="utf-8") as f:
             data = json.load(f)
+    except json.JSONDecodeError as e:
+        print(f"Error parsing JSON file '{p}': {e}")
+        thinking.stop()  # Stop and flush events
+        sys.exit(1)
     except Exception as e:
+        print(f"Unexpected error reading file '{p}': {e}")
         thinking.stop()  # Stop and flush events
-        raise
+        sys.exit(1)
 
 if __name__ == "__main__":
     main()
