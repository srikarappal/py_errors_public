diff --git a/basic_errors/regex_processing_error_scenario.py b/basic_errors/regex_processing_error_scenario.py
index 29530f9..de5af6e 100644
--- a/basic_errors/regex_processing_error_scenario.py
+++ b/basic_errors/regex_processing_error_scenario.py
@@ -6,6 +6,9 @@ except ImportError:
 thinking.start(config_file="thinkingsdk.yaml")
 
 import re
-m = re.match(r"id=(\d+)", "prefix id=42")  # match anchors at start of string
-print(m.group(1))  # AttributeError: 'NoneType' object has no attribute 'group'
+m = re.search(r"id=(\d+)", "prefix id=42")  # search finds pattern anywhere in string
+if m:
+    print(m.group(1))
+else:
+    print("No match found")
 
