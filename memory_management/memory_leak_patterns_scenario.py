"""
Memory leak patterns scenario.
Tests various types of memory leaks that ThinkingSDK should detect and help fix.
"""

import thinking_sdk_client as thinking
import gc
import weakref
import threading
import time
import psutil
import os
from collections import defaultdict
import sys

thinking.start(config_file="thinkingsdk.yaml")

class CircularReferenceLeaker:
    """Demonstrates circular reference memory leaks"""
    
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None
        self.data = [i for i in range(1000)]  # Some data to make leak visible
    
    def add_child(self, child):
        """Create circular reference"""
        child.parent = self  # Child points to parent
        self.children.append(child)  # Parent points to child
        # This creates circular reference that can prevent GC

class EventListenerLeaker:
    """Demonstrates event listener memory leaks"""
    
    def __init__(self):
        self.listeners = defaultdict(list)
        self.data = {}
    
    def add_listener(self, event_type, callback):
        """Add event listener"""
        self.listeners[event_type].append(callback)
    
    def emit_event(self, event_type, data):
        """Emit event to all listeners"""
        for callback in self.listeners[event_type]:
            try:
                callback(data)
            except:
                pass  # Anti-pattern: Don't remove broken listeners
    
    def create_leaky_listener(self):
        """Create listener that holds references"""
        large_data = [i**2 for i in range(10000)]  # Large data structure
        
        def leaky_callback(event_data):
            # This closure captures large_data
            processed = len(large_data) + len(event_data)
            return processed
        
        self.add_listener('test_event', leaky_callback)
        # Listener holds reference to large_data even after this function returns

class CacheWithoutLimits:
    """Cache that grows without bounds"""
    
    def __init__(self):
        self.cache = {}
        self.access_count = 0
    
    def get(self, key):
        """Get from cache"""
        self.access_count += 1
        return self.cache.get(key)
    
    def put(self, key, value):
        """Put in cache - no size limit!"""
        # Anti-pattern: No size limit, no TTL
        self.cache[key] = {
            'value': value,
            'created': time.time(),
            'access_count': 0
        }
    
    def generate_large_cache_data(self, num_items=1000):
        """Generate large amount of cached data"""
        for i in range(num_items):
            key = f"cache_key_{i}"
            value = {
                'data': [j**2 for j in range(1000)],  # Large value
                'metadata': f"metadata_for_item_{i}",
                'timestamp': time.time()
            }
            self.put(key, value)

class ThreadLocalLeaker:
    """Demonstrates thread-local storage leaks"""
    
    def __init__(self):
        self.thread_local_data = threading.local()
        self.thread_counter = 0
    
    def create_thread_data(self):
        """Create thread-local data"""
        self.thread_counter += 1
        
        # Create large data structure in thread-local storage
        self.thread_local_data.large_data = [i for i in range(50000)]
        self.thread_local_data.metadata = {
            'thread_id': threading.get_ident(),
            'created': time.time(),
            'counter': self.thread_counter
        }
    
    def worker_thread(self, worker_id):
        """Worker thread that creates thread-local data"""
        try:
            print(f"Worker-{worker_id}: Creating thread-local data...")
            self.create_thread_data()
            
            # Process work
            time.sleep(1)
            
            # Access thread-local data
            data_size = len(self.thread_local_data.large_data)
            print(f"Worker-{worker_id}: Thread-local data size: {data_size}")
            
            # Anti-pattern: Don't explicitly clean up thread-local data
            # When thread exits, thread-local data might not be immediately GC'd
            
        except Exception as e:
            print(f"🚨 Worker-{worker_id} exception: {e}")

def monitor_memory_usage():
    """Monitor memory usage over time"""
    process = psutil.Process()
    
    return {
        'rss_mb': process.memory_info().rss / 1024 / 1024,
        'vms_mb': process.memory_info().vms / 1024 / 1024,
        'percent': process.memory_percent(),
        'timestamp': time.time()
    }

def test_circular_reference_leak():
    """Test circular reference memory leak"""
    print("🔄 Testing circular reference memory leak...")
    
    initial_memory = monitor_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.1f} MB")
    
    # Create circular references
    root_objects = []
    
    for i in range(100):  # Create many circular reference chains
        root = CircularReferenceLeaker(f"root_{i}")
        
        # Create circular reference chain
        current = root
        for j in range(10):  # 10 levels deep
            child = CircularReferenceLeaker(f"child_{i}_{j}")
            current.add_child(child)
            current = child
        
        # Create circular reference back to root
        current.parent = root
        root_objects.append(root)
    
    after_creation_memory = monitor_memory_usage()
    print(f"After creating circular refs: {after_creation_memory['rss_mb']:.1f} MB")
    
    # Clear references
    root_objects.clear()
    
    # Force garbage collection
    collected = gc.collect()
    print(f"GC collected {collected} objects")
    
    after_gc_memory = monitor_memory_usage()
    print(f"After GC: {after_gc_memory['rss_mb']:.1f} MB")
    
    # Check if memory was properly released
    memory_leak = after_gc_memory['rss_mb'] - initial_memory['rss_mb']
    if memory_leak > 5:  # More than 5MB not released
        raise MemoryError(f"Circular reference memory leak detected: {memory_leak:.1f} MB not released")
    
    return memory_leak

def test_event_listener_leak():
    """Test event listener memory leak"""
    print("🎧 Testing event listener memory leak...")
    
    initial_memory = monitor_memory_usage()
    
    emitter = EventListenerLeaker()
    
    # Create fewer leaky listeners for faster execution
    for i in range(50):
        emitter.create_leaky_listener()
    
    # Emit fewer events to trigger listeners
    for i in range(10):
        emitter.emit_event('test_event', {'data': f'event_{i}'})
    
    after_listeners_memory = monitor_memory_usage()
    memory_used = after_listeners_memory['rss_mb'] - initial_memory['rss_mb']
    
    print(f"Memory used by event listeners: {memory_used:.1f} MB")
    
    # Clear the emitter
    del emitter
    
    # Force GC
    gc.collect()
    
    after_cleanup_memory = monitor_memory_usage()
    memory_leaked = after_cleanup_memory['rss_mb'] - initial_memory['rss_mb']
    
    if memory_leaked > 2:  # More than 2MB not released
        raise MemoryError(f"Event listener memory leak: {memory_leaked:.1f} MB not released")
    
    return memory_leaked

def test_unbounded_cache_leak():
    """Test unbounded cache memory leak"""
    print("💾 Testing unbounded cache memory leak...")
    
    initial_memory = monitor_memory_usage()
    
    cache = CacheWithoutLimits()
    
    # Fill cache with smaller amount of data for faster execution
    print("Generating cache data...")
    cache.generate_large_cache_data(200)  # 200 items
    
    after_cache_memory = monitor_memory_usage()
    cache_memory = after_cache_memory['rss_mb'] - initial_memory['rss_mb']
    
    print(f"Cache using {cache_memory:.1f} MB")
    print(f"Cache size: {len(cache.cache)} items")
    
    # Process cache that never expires items
    print("Adding more items to unbounded cache...")
    for i in range(1000):
        key = f"extra_key_{i}"
        large_value = [j for j in range(5000)]  # Large value
        cache.put(key, large_value)
    
    final_memory = monitor_memory_usage()
    total_cache_memory = final_memory['rss_mb'] - initial_memory['rss_mb']
    
    print(f"Final cache memory: {total_cache_memory:.1f} MB")
    
    if total_cache_memory > 20:  # Cache using too much memory
        raise MemoryError(f"Unbounded cache memory leak: {total_cache_memory:.1f} MB used")
    
    return total_cache_memory

def test_thread_local_leak():
    """Test thread-local storage memory leak"""
    print("🧵 Testing thread-local storage memory leak...")
    
    initial_memory = monitor_memory_usage()
    
    leaker = ThreadLocalLeaker()
    
    # Create fewer threads for faster execution
    threads = []
    num_threads = 10
    
    for i in range(num_threads):
        thread = threading.Thread(target=leaker.worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    after_threads_memory = monitor_memory_usage()
    thread_memory = after_threads_memory['rss_mb'] - initial_memory['rss_mb']
    
    print(f"Memory after {num_threads} threads: {thread_memory:.1f} MB")
    
    # Clear references and force GC
    threads.clear()
    del leaker
    
    # Multiple GC cycles to clean up thread-local data
    for _ in range(3):
        gc.collect()
        time.sleep(0.1)
    
    final_memory = monitor_memory_usage()
    memory_leaked = final_memory['rss_mb'] - initial_memory['rss_mb']
    
    print(f"Memory after cleanup: {memory_leaked:.1f} MB")
    
    if memory_leaked > 3:  # More than 3MB not released
        raise MemoryError(f"Thread-local storage leak: {memory_leaked:.1f} MB not released")
    
    return memory_leaked

def test_global_state_accumulation():
    """Test global state accumulation over time"""
    print("🌍 Testing global state accumulation...")
    
    # Process global variables that accumulate data
    if not hasattr(sys.modules[__name__], 'GLOBAL_DATA_STORE'):
        sys.modules[__name__].GLOBAL_DATA_STORE = {}
    
    if not hasattr(sys.modules[__name__], 'GLOBAL_REQUEST_LOG'):
        sys.modules[__name__].GLOBAL_REQUEST_LOG = []
    
    initial_memory = monitor_memory_usage()
    
    # Process application adding data to global state
    for i in range(100):
        # Add to global data store (anti-pattern: never cleaned)
        key = f"global_key_{i}"
        value = {
            'data': [j**2 for j in range(100)],
            'created': time.time(),
            'request_id': f"req_{i}"
        }
        sys.modules[__name__].GLOBAL_DATA_STORE[key] = value
        
        # Add to global request log (anti-pattern: never cleaned)
        log_entry = {
            'request_id': f"req_{i}",
            'timestamp': time.time(),
            'data_size': len(value['data'])
        }
        sys.modules[__name__].GLOBAL_REQUEST_LOG.append(log_entry)
    
    after_globals_memory = monitor_memory_usage()
    global_memory = after_globals_memory['rss_mb'] - initial_memory['rss_mb']
    
    print(f"Global state using {global_memory:.1f} MB")
    print(f"Global data store size: {len(sys.modules[__name__].GLOBAL_DATA_STORE)}")
    print(f"Global request log size: {len(sys.modules[__name__].GLOBAL_REQUEST_LOG)}")
    
    if global_memory > 5:  # Global state using too much memory
        raise MemoryError(f"Global state accumulation: {global_memory:.1f} MB used")
    
    return global_memory

def main():
    print("🚨 Starting memory leak patterns scenario...")
    
    memory_leaks_detected = []
    
    try:
        # Test different types of memory leaks
        leak_tests = [
            ("Circular References", test_circular_reference_leak),
            ("Event Listeners", test_event_listener_leak), 
            ("Unbounded Cache", test_unbounded_cache_leak),
            ("Thread-Local Storage", test_thread_local_leak),
            ("Global State Accumulation", test_global_state_accumulation)
        ]
        
        for test_name, test_func in leak_tests:
            print(f"\n=== {test_name} Test ===")
            
            try:
                memory_leaked = test_func()
                print(f"✅ {test_name}: {memory_leaked:.1f} MB impact")
                
            except MemoryError as e:
                print(f"🚨 {test_name} LEAK DETECTED: {e}")
                memory_leaks_detected.append((test_name, str(e)))
                
            except Exception as e:
                print(f"🚨 {test_name} test error: {e}")
        
        # Final summary
        print(f"\n📊 Memory Leak Detection Summary:")
        print(f"   Tests completed: {len(leak_tests)}")
        print(f"   Leaks detected: {len(memory_leaks_detected)}")
        
        if memory_leaks_detected:
            print("🚨 Memory leaks detected:")
            for leak_name, leak_desc in memory_leaks_detected:
                print(f"   • {leak_name}: {leak_desc}")
            
            # Raise final exception with all detected leaks
            leak_summary = "; ".join([f"{name}: {desc}" for name, desc in memory_leaks_detected])
            raise MemoryError(f"Multiple memory leaks detected: {leak_summary}")
        
        print("✅ No significant memory leaks detected")
        
    except Exception as e:
        print(f"🚨 Memory leak scenario exception: {e}")
        time.sleep(2)
        raise

if __name__ == "__main__":
    try:
        main()
        print("✅ Memory leak patterns scenario completed!")
    except Exception as e:
        print(f"🚨 Memory leak patterns scenario failed: {e}")
    finally:
        print("Stopping ThinkingSDK...")
        thinking.stop()
        print("Check ThinkingSDK server for memory leak pattern analysis!")