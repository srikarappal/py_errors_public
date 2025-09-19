diff --git a/basic_errors/nonetype_attribute_error_scenario.py b/basic_errors/nonetype_attribute_error_scenario.py
index 726f103..b13b9ea 100644
--- a/basic_errors/nonetype_attribute_error_scenario.py
+++ b/basic_errors/nonetype_attribute_error_scenario.py
@@ -1,3 +1,5 @@
+import sys
+
 try:
     import thinking_sdk_client as thinking
 except ImportError:
@@ -6,5 +8,5 @@ except ImportError:
 thinking.start(config_file="thinkingsdk.yaml")
 
 names = []
-names = names.append("Ada")   # .append returns None
-print(len(names))             # TypeError: object of type 'NoneType' has no len()
+names.append("Ada")   # .append modifies list in-place
+print(len(names))             # Should print: 1
