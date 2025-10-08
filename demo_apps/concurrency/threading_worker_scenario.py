import thinking_sdk_client as thinking
thinking.start(config_file="thinkingsdk.yaml")

import threading

count = 0

def worker(n=10_000):
    global count
    for _ in range(n):
        count += 1  # not atomic → races

threads = [threading.Thread(target=worker) for _ in range(200)]
[t.start() for t in threads]
[t.join() for t in threads]

# Often prints less than 200_000
assert count == 20 * 10_000, f"Lost updates! got {count}"
