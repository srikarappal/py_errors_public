import thinking_sdk_client as thinking
thinking.start(config_file="thinkingsdk.yaml")

arr = [1, 2, 3]
for i in range(len(arr)):
    print(arr[i + 1])  # IndexError on last iteration (i = 2 -> i+1 = 3 out of range)
