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
index dcb85f4..0c8771d 100644
--- a/basic_errors/json_file_processing_scenario.py
+++ b/basic_errors/json_file_processing_scenario.py
@@ -24,7 +24,7 @@ def main():
     
 
     data = {}
-    p = Path("first_process_parsing_config.json")
+    p = Path("first_scenario_parsing_config.json")
     if not p.exists():
         
         sys.exit(1)
