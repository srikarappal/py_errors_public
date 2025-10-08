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
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        
        
        # Process work that might fail
        for i in range(5):
            
            time.sleep(0.1)
            
            # Introduce errors in some workers
            if worker_id == 2 and i == 3:
                # This should be captured by ThinkingSDK
                raise ValueError(f"Worker-{worker_id}: Processd processing error at item {i}")
            
            # Access shared data (potential race condition)
            shared_data[worker_id] = f"Worker-{worker_id} completed item {i}"
        
        
        return f"Worker-{worker_id} finished"
        
    except Exception as e:
        
        time.sleep(1)
        raise
        
    finally:
        
        thinking.stop()
        time.sleep(0.5)  # Give time to flush

def main():
    
    
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
            
        
        # Wait for all processes to complete
        for i, process in enumerate(processes):
            process.join(timeout=10)  # 10 second timeout
            
            if process.is_alive():
                
                process.terminate()
                process.join(timeout=5)
                
                if process.is_alive():
                    
                    process.kill()
                    
                raise TimeoutError(f"Worker-{i} failed to complete within timeout")
            
            
            if process.exitcode != 0:
        
        for key, value in shared_data.items():
            
            
    except Exception as e:
        
        time.sleep(2)
        raise
        
    finally:
        
        thinking.stop()

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.set_start_method('spawn', force=True) if sys.platform == 'win32' else None
    
    try:
        main()
    except Exception as e:
    