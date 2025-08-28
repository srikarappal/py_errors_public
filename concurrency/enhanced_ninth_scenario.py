"""
Enhanced deadlock scenario with ThinkingSDK integration.
Shows how ThinkingSDK can detect deadlock patterns even when no exception occurs.
"""

import thinking_sdk_client as thinking
import threading
import time
import sys

# Start ThinkingSDK with enhanced threading support
thinking.start(config_file="thinkingsdk.yaml")

# Global locks that will cause deadlock
lock_a = threading.Lock()
lock_b = threading.Lock()

# Shared state for coordination
thread_states = {
    "t1_acquired_a": False,
    "t2_acquired_b": False,
    "deadlock_detected": False
}

def thread_1():
    """Thread 1: Acquires lock_a, then lock_b"""
    try:
        print(f"Thread-1: Attempting to acquire lock_a")
        
        # This is the key insight: We'll add timeouts to detect deadlock
        if lock_a.acquire(timeout=2.0):  # 2 second timeout
            thread_states["t1_acquired_a"] = True
            print(f"Thread-1: Acquired lock_a, sleeping...")
            
            time.sleep(0.1)  # Give thread-2 time to acquire lock_b
            
            print(f"Thread-1: Attempting to acquire lock_b")
            if lock_b.acquire(timeout=1.0):  # This will timeout in deadlock
                print(f"Thread-1: Acquired both locks!")
                lock_b.release()
            else:
                # This exception WILL be captured by ThinkingSDK
                raise TimeoutError("Thread-1: Deadlock detected - couldn't acquire lock_b")
                
            lock_a.release()
        else:
            raise TimeoutError("Thread-1: Couldn't acquire lock_a")
            
    except Exception as e:
        print(f"Thread-1 Exception: {e}")
        thread_states["deadlock_detected"] = True
        raise  # Re-raise so ThinkingSDK captures it

def thread_2():
    """Thread 2: Acquires lock_b, then lock_a"""
    try:
        print(f"Thread-2: Attempting to acquire lock_b")
        
        if lock_b.acquire(timeout=2.0):  # 2 second timeout
            thread_states["t2_acquired_b"] = True
            print(f"Thread-2: Acquired lock_b, sleeping...")
            
            time.sleep(0.1)  # Give thread-1 time to acquire lock_a
            
            print(f"Thread-2: Attempting to acquire lock_a")
            if lock_a.acquire(timeout=1.0):  # This will timeout in deadlock
                print(f"Thread-2: Acquired both locks!")
                lock_a.release()
            else:
                # This exception WILL be captured by ThinkingSDK
                raise TimeoutError("Thread-2: Deadlock detected - couldn't acquire lock_a")
                
            lock_b.release()
        else:
            raise TimeoutError("Thread-2: Couldn't acquire lock_b")
            
    except Exception as e:
        print(f"Thread-2 Exception: {e}")
        thread_states["deadlock_detected"] = True
        raise  # Re-raise so ThinkingSDK captures it

def main():
    print("🚨 Starting deadlock scenario with ThinkingSDK monitoring...")
    
    # Create threads
    t1 = threading.Thread(target=thread_1, name="DeadlockThread-1")
    t2 = threading.Thread(target=thread_2, name="DeadlockThread-2")
    
    # Start threads
    t1.start()
    t2.start()
    
    # Join with timeout to avoid hanging the main thread
    t1.join(timeout=5.0)
    t2.join(timeout=5.0)
    
    # Check if threads are still alive (deadlock detection)
    if t1.is_alive() or t2.is_alive():
        print("🚨 DEADLOCK DETECTED: Threads are still running after timeout!")
        
        # Force terminate threads (in real apps, this would be handled differently)
        # For testing purposes, we'll create an artificial exception
        raise RuntimeError("Deadlock detected: Threads failed to complete within timeout")
    
    if thread_states["deadlock_detected"]:
        print("✅ Deadlock successfully detected and reported to ThinkingSDK!")
    else:
        print("❌ No deadlock occurred - both threads completed successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"🚨 Main thread exception: {e}")
        # Give ThinkingSDK time to flush the exception
        time.sleep(2)
    finally:
        # Ensure ThinkingSDK processes all events
        thinking.stop()
        print("ThinkingSDK stopped. Check server for deadlock analysis!")