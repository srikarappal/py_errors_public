"""
Thread resource leak scenario that ThinkingSDK can help detect.
Shows how improper thread management can cause resource exhaustion.
"""

import thinking_sdk_client as thinking
import threading
import time
import psutil
import os

# Start ThinkingSDK
thinking.start(config_file="thinkingsdk.yaml")

def leaky_worker(worker_id):
    """Worker that processs work but has resource management issues"""
    try:
        
        
        # Process work with potential to hang
        work_duration = 0.1
        start_time = time.time()
        
        while time.time() - start_time < work_duration:
            # Process CPU work
            _ = sum(i * i for i in range(1000))
        
        
        
        # Process a condition where some threads might hang
        if worker_id % 7 == 0:  # Every 7th thread has issues
            
            time.sleep(10)  # This will cause thread to hang
            
    except Exception as e:
        raise

def monitor_resources():
    """Monitor system resources for thread leaks"""
    process = psutil.Process(os.getpid())
    
    return {
        "thread_count": process.num_threads(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
        "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
    }

def main():
    
    initial_resources = monitor_resources()
    
    
    threads = []
    max_threads = 20
    thread_timeout = 2.0  # Threads should complete within 2 seconds
    
    try:
        # Create many threads
        for i in range(max_threads):
            thread = threading.Thread(
                target=leaky_worker,
                args=(i,),
                name=f"LeakyWorker-{i}"
            )
            threads.append(thread)
            thread.start()
            
            # Monitor resource growth
            if i % 5 == 0:
                current_resources = monitor_resources()
                
        
        
        
        # Wait for threads with timeout
        completed_threads = 0
        hung_threads = []
        
        for i, thread in enumerate(threads):
            thread.join(timeout=thread_timeout)
            
            if thread.is_alive():
                hung_threads.append((i, thread))
            else:
                completed_threads += 1
        
        final_resources = monitor_resources()
        
        
        # Analyze resource leaks
        thread_leak_count = len(hung_threads)
        memory_increase = final_resources["memory_mb"] - initial_resources["memory_mb"]
        thread_increase = final_resources["thread_count"] - initial_resources["thread_count"]
        
        
        
        
        
        
        
        if thread_leak_count > 0:
            raise ResourceWarning(f"THREAD LEAK DETECTED: {thread_leak_count} threads failed to complete. "
                                f"Memory increased by {memory_increase:.2f} MB. "
                                f"Net thread count increased by {thread_increase}.")
        
        if memory_increase > 50:  # More than 50MB increase
            raise MemoryError(f"MEMORY LEAK DETECTED: Memory increased by {memory_increase:.2f} MB")
            
    except Exception as e:
        raise
    
    finally:
        # Cleanup: Force terminate hung threads (not recommended in production)
        for i, thread in hung_threads:
            
            # Note: Python doesn't have thread.terminate(), this is just for illustration

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        time.sleep(2)  
    finally:
        thinking.stop()