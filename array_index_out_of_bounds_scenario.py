diff --git a/basic_errors/array_index_out_of_bounds_scenario.py b/basic_errors/array_index_out_of_bounds_scenario.py
index 63329f0..2729f64 100644
--- a/basic_errors/array_index_out_of_bounds_scenario.py
+++ b/basic_errors/array_index_out_of_bounds_scenario.py
@@ -3,4 +3,4 @@ thinking.start(config_file="thinkingsdk.yaml")
 
 arr = [1, 2, 3]
 for i in range(len(arr)):
-    print(arr[i + 1])  # IndexError on last iteration (i = 2 -> i+1 = 3 out of range)
+    print(arr[i])  # Fixed: access current element instead of next element
