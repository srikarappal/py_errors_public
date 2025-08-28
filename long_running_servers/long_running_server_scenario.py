"""
Long-running server scenarios that test resource leaks, memory growth, and degradation over time.
These scenarios simulate real production server issues that only manifest after hours/days of runtime.
"""

import thinking_sdk_client as thinking
import threading
import time
import psutil
import os
import gc
import weakref
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from concurrent.futures import ThreadPoolExecutor
import json
import random
from collections import deque, defaultdict

thinking.start(config_file="thinkingsdk.yaml")

class MemoryLeakyHandler(BaseHTTPRequestHandler):
    """HTTP handler that demonstrates memory leaks"""
    
    # Class-level collections that grow over time (anti-pattern)
    request_history = []  # Never cleared - grows indefinitely
    user_sessions = {}    # Sessions never expire
    cached_responses = {} # Cache without TTL or size limits
    
    def do_GET(self):
        """Handle GET requests with memory leaks"""
        try:
            # Memory leak pattern 1: Accumulating request history
            request_info = {
                'timestamp': time.time(),
                'path': self.path,
                'client': self.client_address[0],
                'headers': dict(self.headers),
                'thread_id': threading.get_ident()
            }
            
            # This list grows forever (anti-pattern)
            self.request_history.append(request_info)
            
            # Memory leak pattern 2: Sessions without expiration
            session_id = self.headers.get('Session-ID', f"session_{len(self.user_sessions)}")
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    'created': time.time(),
                    'requests': [],
                    'data': {}
                }
            
            # Accumulate session data (anti-pattern)
            self.user_sessions[session_id]['requests'].append(request_info)
            
            # Memory leak pattern 3: Unbounded cache
            cache_key = f"{self.path}_{hash(str(self.headers))}"
            if cache_key not in self.cached_responses:
                # Simulate expensive computation
                expensive_data = {
                    'computation_result': [i**2 for i in range(1000)],  # Large data
                    'metadata': {
                        'computed_at': time.time(),
                        'request_path': self.path,
                        'session_id': session_id
                    }
                }
                # Cache grows forever (anti-pattern)
                self.cached_responses[cache_key] = expensive_data
            
            # Simulate response
            if self.path == '/health':
                response_data = {
                    'status': 'ok',
                    'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                    'active_sessions': len(self.user_sessions),
                    'request_history_size': len(self.request_history),
                    'cache_size': len(self.cached_responses)
                }
            elif self.path == '/heavy-computation':
                # Simulate CPU-intensive work that creates objects
                result = self._heavy_computation()
                response_data = {'result': result}
            else:
                response_data = {'message': f'Response for {self.path}'}
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            print(f"🚨 Handler exception: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal server error: {e}".encode())
    
    def _heavy_computation(self):
        """Simulate heavy computation that might leak memory"""
        # Create large temporary objects
        large_lists = []
        
        for i in range(100):
            # Create large list
            data = [random.random() for _ in range(10000)]
            large_lists.append(data)
            
            # Some lists "accidentally" escape garbage collection
            if i % 10 == 0:
                # Store reference in class variable (anti-pattern)
                if not hasattr(self.__class__, '_computation_cache'):
                    self.__class__._computation_cache = []
                self.__class__._computation_cache.append(data)
        
        # Return summary (but large_lists and some data leaked)
        return {
            'processed_items': len(large_lists),
            'cache_size': len(getattr(self.__class__, '_computation_cache', [])),
            'memory_peak_estimate': '~100MB'
        }
    
    def log_message(self, format, *args):
        """Override to reduce log spam"""
        pass

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP Server with threading support"""
    daemon_threads = True  # Important: prevents hanging on shutdown

class LongRunningServerMonitor:
    """Monitor server health over time"""
    
    def __init__(self, server_port):
        self.server_port = server_port
        self.start_time = time.time()
        self.monitoring = False
        self.metrics_history = deque(maxlen=100)  # Keep last 100 readings
        self.alert_thresholds = {
            'memory_mb': 200,  # Alert if memory > 200MB
            'thread_count': 50,  # Alert if threads > 50
            'response_time_ms': 1000  # Alert if response > 1s
        }
    
    def start_monitoring(self):
        """Start monitoring server health"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        print("📊 Server monitoring started...")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Log metrics periodically
                if len(self.metrics_history) % 10 == 0:
                    self._log_metrics(metrics)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"🚨 Monitoring error: {e}")
                time.sleep(5)
    
    def _collect_metrics(self):
        """Collect current server metrics"""
        process = psutil.Process()
        
        # Test server responsiveness
        response_time = self._test_server_response()
        
        return {
            'timestamp': time.time(),
            'uptime_seconds': time.time() - self.start_time,
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'thread_count': process.num_threads(),
            'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0,
            'response_time_ms': response_time,
            'handler_metrics': {
                'request_history_size': len(MemoryLeakyHandler.request_history),
                'active_sessions': len(MemoryLeakyHandler.user_sessions),
                'cache_size': len(MemoryLeakyHandler.cached_responses)
            }
        }
    
    def _test_server_response(self):
        """Test server response time"""
        try:
            start_time = time.time()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            
            sock.connect(('localhost', self.server_port))
            request = b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n"
            sock.send(request)
            
            response = sock.recv(1024)
            sock.close()
            
            response_time = (time.time() - start_time) * 1000
            return response_time
            
        except Exception as e:
            print(f"⚠️ Server response test failed: {e}")
            return 9999  # Indicates server unresponsive
    
    def _check_alerts(self, metrics):
        """Check if any metrics exceed thresholds"""
        alerts = []
        
        if metrics['memory_mb'] > self.alert_thresholds['memory_mb']:
            alerts.append(f"HIGH MEMORY: {metrics['memory_mb']:.1f}MB (threshold: {self.alert_thresholds['memory_mb']}MB)")
        
        if metrics['thread_count'] > self.alert_thresholds['thread_count']:
            alerts.append(f"HIGH THREAD COUNT: {metrics['thread_count']} (threshold: {self.alert_thresholds['thread_count']})")
        
        if metrics['response_time_ms'] > self.alert_thresholds['response_time_ms']:
            alerts.append(f"SLOW RESPONSE: {metrics['response_time_ms']:.1f}ms (threshold: {self.alert_thresholds['response_time_ms']}ms)")
        
        # Check for memory growth trend
        if len(self.metrics_history) >= 5:
            recent_memory = [m['memory_mb'] for m in list(self.metrics_history)[-5:]]
            if self._is_growing_trend(recent_memory, threshold=10):  # 10MB increase trend
                alerts.append(f"MEMORY LEAK DETECTED: Memory growing trend {recent_memory}")
        
        # Trigger alerts
        for alert in alerts:
            print(f"🚨 ALERT: {alert}")
            # In real scenario, this would trigger ThinkingSDK exception
            if "MEMORY LEAK" in alert:
                raise MemoryError(f"Memory leak detected in long-running server: {alert}")
    
    def _is_growing_trend(self, values, threshold=5):
        """Check if values show growing trend"""
        if len(values) < 3:
            return False
        
        growth = values[-1] - values[0]
        return growth > threshold
    
    def _log_metrics(self, metrics):
        """Log current metrics"""
        uptime_hours = metrics['uptime_seconds'] / 3600
        print(f"📊 Server Health (uptime: {uptime_hours:.1f}h):")
        print(f"   Memory: {metrics['memory_mb']:.1f}MB | Threads: {metrics['thread_count']} | CPU: {metrics['cpu_percent']:.1f}%")
        print(f"   Response: {metrics['response_time_ms']:.1f}ms | Sessions: {metrics['handler_metrics']['active_sessions']}")
        print(f"   Request History: {metrics['handler_metrics']['request_history_size']} | Cache: {metrics['handler_metrics']['cache_size']}")

def load_test_server(server_port, duration_seconds=60, concurrent_clients=5):
    """Run load test against the server"""
    
    print(f"🔥 Starting load test: {concurrent_clients} clients for {duration_seconds}s")
    
    def client_worker(client_id):
        """Individual client worker"""
        session_id = f"load_test_session_{client_id}"
        requests_made = 0
        
        endpoints = ['/health', '/data', '/heavy-computation', '/api/users', '/api/orders']
        
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            try:
                endpoint = random.choice(endpoints)
                
                # Make HTTP request
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect(('localhost', server_port))
                
                request = f"GET {endpoint} HTTP/1.1\r\nHost: localhost\r\nSession-ID: {session_id}\r\n\r\n"
                sock.send(request.encode())
                
                response = sock.recv(4096)
                sock.close()
                
                requests_made += 1
                
                # Random delay between requests
                time.sleep(random.uniform(0.1, 1.0))
                
            except Exception as e:
                print(f"🚨 Client-{client_id} error: {e}")
                time.sleep(1)
        
        print(f"Client-{client_id}: Made {requests_made} requests in {duration_seconds}s")
        return requests_made
    
    # Run concurrent clients
    with ThreadPoolExecutor(max_workers=concurrent_clients) as executor:
        futures = [executor.submit(client_worker, i) for i in range(concurrent_clients)]
        
        total_requests = 0
        for future in futures:
            try:
                requests = future.result()
                total_requests += requests
            except Exception as e:
                print(f"🚨 Load test client failed: {e}")
    
    print(f"🔥 Load test completed: {total_requests} total requests")
    return total_requests

def main():
    print("🚨 Starting long-running server scenario...")
    
    # Start server
    server_port = 8765
    print(f"🚀 Starting HTTP server on port {server_port}...")
    
    try:
        server = ThreadingHTTPServer(('localhost', server_port), MemoryLeakyHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        print(f"✅ Server started successfully")
        
        # Start monitoring
        monitor = LongRunningServerMonitor(server_port)
        monitor.start_monitoring()
        
        # Run load tests in phases
        test_phases = [
            (30, 2, "Warm-up phase"),
            (60, 5, "Normal load phase"), 
            (45, 10, "High load phase"),
            (30, 3, "Cool-down phase")
        ]
        
        for duration, clients, phase_name in test_phases:
            print(f"\n🔄 {phase_name}: {clients} clients for {duration}s")
            
            try:
                requests_made = load_test_server(server_port, duration, clients)
                print(f"✅ {phase_name} completed: {requests_made} requests")
                
                # Brief pause between phases
                time.sleep(5)
                
            except Exception as e:
                print(f"🚨 {phase_name} failed: {e}")
        
        # Final monitoring check
        print("\n📊 Final server health check...")
        time.sleep(10)
        
        # Force garbage collection and check if memory was released
        print("🗑️ Forcing garbage collection...")
        gc.collect()
        time.sleep(5)
        
        final_metrics = monitor._collect_metrics()
        print(f"📊 Final metrics: {final_metrics['memory_mb']:.1f}MB, {final_metrics['handler_metrics']}")
        
        # Check for memory that wasn't released
        if final_metrics['memory_mb'] > 100:  # Arbitrary threshold
            raise ResourceWarning(f"Server memory usage still high after GC: {final_metrics['memory_mb']:.1f}MB")
        
    except Exception as e:
        print(f"🚨 Long-running server scenario exception: {e}")
        time.sleep(2)
        raise
    
    finally:
        print("🛑 Shutting down server...")
        if 'monitor' in locals():
            monitor.stop_monitoring()
        if 'server' in locals():
            server.shutdown()
            server.server_close()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
        print("✅ Long-running server scenario completed!")
    except Exception as e:
        print(f"🚨 Long-running server scenario failed: {e}")
    finally:
        print("Stopping ThinkingSDK...")
        thinking.stop()
        print("Check ThinkingSDK server for long-running server analysis!")