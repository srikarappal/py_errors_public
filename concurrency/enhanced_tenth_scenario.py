"""
Enhanced threading condition variable scenario with ThinkingSDK integration.
Shows how ThinkingSDK can capture threading errors with proper exception handling.
"""

import thinking_sdk_client as thinking
import threading
import time
import sys
import traceback

# Start ThinkingSDK
thinking.start(config_file="thinkingsdk.yaml")

# Shared resources
cv = threading.Condition()
data_ready = False
producer_error = None
consumer_error = None

def producer():
    """Producer that incorrectly uses condition variable"""
    global data_ready, producer_error
    
    try:
        
        time.sleep(0.1)  # Process work
        
        
        data_ready = True
        
        # This will raise RuntimeError: cannot notify on un-owned lock
        cv.notify()  # BUG: Should be cv.notify() inside with cv: block
        
        
        
    except Exception as e:
        producer_error = e
        traceback.print_exc()
        
        # Ensure the exception gets to ThinkingSDK by re-raising
        raise

def consumer():
    """Consumer that waits for data"""
    global consumer_error
    
    try:
        
        
        with cv:
            timeout_count = 0
            while not data_ready:
                
                
                # Wait with timeout to avoid hanging forever
                if cv.wait(timeout=2.0):
                    
                    break
                else:
                    timeout_count += 1
                    if timeout_count >= 3:
                        raise TimeoutError("Consumer: Timed out waiting for producer notification")
        
        if data_ready:
            
            time.sleep(0.1)  # Process processing
            
        
    except Exception as e:
        consumer_error = e
        traceback.print_exc()
        raise

def thread_exception_handler(args):
    """Custom thread exception handler to ensure ThinkingSDK captures thread exceptions"""
    
    
    
    
    # This ensures the exception is visible to the main thread
    # and gets processed by ThinkingSDK
    if args.thread.name == "ProducerThread":
        global producer_error
        producer_error = args.exc_value
    elif args.thread.name == "ConsumerThread":
        global consumer_error  
        consumer_error = args.exc_value

def main():
    
    # Install custom thread exception handler
    threading.excepthook = thread_exception_handler
    
    # Create threads
    consumer_thread = threading.Thread(target=consumer, name="ConsumerThread")
    producer_thread = threading.Thread(target=producer, name="ProducerThread")
    
    # Start consumer first (it will wait)
    consumer_thread.start()
    time.sleep(0.05)  # Give consumer time to start waiting
    
    # Start producer (this will trigger the error)
    producer_thread.start()
    
    # Wait for threads to complete
    producer_thread.join(timeout=5.0)
    consumer_thread.join(timeout=5.0) 
    
    # Check for exceptions
    if producer_error:
        # Re-raise in main thread so ThinkingSDK definitely captures it
        raise RuntimeError(f"Producer thread failed: {producer_error}")
    
    if consumer_error:
        raise RuntimeError(f"Consumer thread failed: {consumer_error}")
    
    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        
        
        # Give ThinkingSDK extra time to process the exception
        time.sleep(2)
        
    finally:
        thinking.stop()
        
        # Extra sleep to ensure all events are flushed
        time.sleep(1)