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
        print("Producer: Starting data production...")
        time.sleep(0.1)  # Process work
        
        print("Producer: Data ready, attempting to notify...")
        data_ready = True
        
        # This will raise RuntimeError: cannot notify on un-owned lock
        cv.notify()  # BUG: Should be cv.notify() inside with cv: block
        
        print("Producer: Successfully notified consumers")
        
    except Exception as e:
        producer_error = e
        print(f"🚨 Producer Exception: {e}")
        print(f"🚨 Producer Traceback:")
        traceback.print_exc()
        
        # Ensure the exception gets to ThinkingSDK by re-raising
        raise

def consumer():
    """Consumer that waits for data"""
    global consumer_error
    
    try:
        print("Consumer: Starting, waiting for data...")
        
        with cv:
            timeout_count = 0
            while not data_ready:
                print(f"Consumer: Waiting for data (attempt {timeout_count + 1})...")
                
                # Wait with timeout to avoid hanging forever
                if cv.wait(timeout=2.0):
                    print("Consumer: Received notification!")
                    break
                else:
                    timeout_count += 1
                    if timeout_count >= 3:
                        raise TimeoutError("Consumer: Timed out waiting for producer notification")
        
        if data_ready:
            print("Consumer: Processing data...")
            time.sleep(0.1)  # Process processing
            print("Consumer: Data processed successfully!")
        
    except Exception as e:
        consumer_error = e
        print(f"🚨 Consumer Exception: {e}")
        print(f"🚨 Consumer Traceback:")
        traceback.print_exc()
        raise

def thread_exception_handler(args):
    """Custom thread exception handler to ensure ThinkingSDK captures thread exceptions"""
    print(f"\n🚨 THREAD EXCEPTION HANDLER CALLED:")
    print(f"   Thread: {args.thread}")
    print(f"   Exception: {args.exc_type.__name__}: {args.exc_value}")
    print(f"   Traceback: {args.exc_traceback}")
    
    # This ensures the exception is visible to the main thread
    # and gets processed by ThinkingSDK
    if args.thread.name == "ProducerThread":
        global producer_error
        producer_error = args.exc_value
    elif args.thread.name == "ConsumerThread":
        global consumer_error  
        consumer_error = args.exc_value

def main():
    print("🚨 Starting threading condition variable scenario...")
    
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
        print(f"\n✅ Producer error captured: {producer_error}")
        # Re-raise in main thread so ThinkingSDK definitely captures it
        raise RuntimeError(f"Producer thread failed: {producer_error}")
    
    if consumer_error:
        print(f"\n✅ Consumer error captured: {consumer_error}")
        raise RuntimeError(f"Consumer thread failed: {consumer_error}")
    
    print("❓ No exceptions detected - scenario may need adjustment")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n🚨 Main thread final exception: {e}")
        print("This exception should be captured by ThinkingSDK!")
        
        # Give ThinkingSDK extra time to process the exception
        time.sleep(2)
        
    finally:
        print("\n🔄 Stopping ThinkingSDK...")
        thinking.stop()
        print("✅ ThinkingSDK stopped. Check server for threading error analysis!")
        
        # Extra sleep to ensure all events are flushed
        time.sleep(1)