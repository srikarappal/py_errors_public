"""
Basic multi-process scenario to test ThinkingSDK's current capabilities.
This should work with current implementation.
"""

import thinking_sdk_client as thinking
import multiprocessing
import os
import time
import sys

def worker_process(worker_id, shared_data):
    """Worker process that will be monitored by ThinkingSDK"""
    
    # Initialize ThinkingSDK in this process
    print(f"Worker-{worker_id} (PID: {os.getpid()}): Starting ThinkingSDK...")
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        print(f"Worker-{worker_id}: Starting work...")
        
        # Simulate work that might fail
        for i in range(5):
            print(f"Worker-{worker_id}: Processing item {i}")
            time.sleep(0.1)
            
            # Introduce errors in some workers
            if worker_id == 2 and i == 3:
                # This should be captured by ThinkingSDK
                raise ValueError(f"Worker-{worker_id}: Simulated processing error at item {i}")
            
            # Access shared data (potential race condition)
            shared_data[worker_id] = f"Worker-{worker_id} completed item {i}"
        
        print(f"Worker-{worker_id}: All work completed successfully")
        return f"Worker-{worker_id} finished"
        
    except Exception as e:
        print(f"🚨 Worker-{worker_id} Exception: {e}")
        # Give ThinkingSDK time to process the exception
        time.sleep(1)
        raise
        
    finally:
        print(f"Worker-{worker_id}: Stopping ThinkingSDK...")
        thinking.stop()
        time.sleep(0.5)  # Give time to flush

def main():
    print("🚨 Starting basic multi-process scenario...")
    print(f"Main process PID: {os.getpid()}")
    
    # Start ThinkingSDK in main process
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Shared data structure
        manager = multiprocessing.Manager()
        shared_data = manager.dict()
        
        # Create worker processes
        processes = []
        num_workers = 4
        
        for i in range(num_workers):
            process = multiprocessing.Process(
                target=worker_process,
                args=(i, shared_data),
                name=f"Worker-{i}"
            )
            processes.append(process)
            process.start()
            print(f"Started Worker-{i} with PID: {process.pid}")
        
        # Wait for all processes to complete
        for i, process in enumerate(processes):
            process.join(timeout=10)  # 10 second timeout
            
            if process.is_alive():
                print(f"🚨 Worker-{i} (PID: {process.pid}) timed out, terminating...")
                process.terminate()
                process.join(timeout=5)
                
                if process.is_alive():
                    print(f"🚨 Force killing Worker-{i} (PID: {process.pid})")
                    process.kill()
                    
                raise TimeoutError(f"Worker-{i} failed to complete within timeout")
            
            print(f"Worker-{i} finished with exit code: {process.exitcode}")
            if process.exitcode != 0:
                print(f"🚨 Worker-{i} exited with error code: {process.exitcode}")
        
        print(f"\n📊 Final shared data state:")
        for key, value in shared_data.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"🚨 Main process exception: {e}")
        # Give ThinkingSDK time to process
        time.sleep(2)
        raise
        
    finally:
        print("Main process: Stopping ThinkingSDK...")
        thinking.stop()

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.set_start_method('spawn', force=True) if sys.platform == 'win32' else None
    
    try:
        main()
        print("✅ Multi-process scenario completed successfully!")
    except Exception as e:
        print(f"🚨 Multi-process scenario failed: {e}")
    
    print("Check ThinkingSDK server for multi-process event analysis!")