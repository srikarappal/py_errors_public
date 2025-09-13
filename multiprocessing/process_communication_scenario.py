"""
Multi-process communication scenario to test ThinkingSDK's limitations.
Shows issues with cross-process correlation and IPC error tracking.
"""

import thinking_sdk_client as thinking
import multiprocessing
import multiprocessing.connection
import os
import time
import sys
import socket

def producer_process(conn_send):
    """Producer process that sends data via pipe"""
    
    print(f"Producer (PID: {os.getpid()}): Starting ThinkingSDK...")
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        print("Producer: Starting data production...")
        
        for i in range(10):
            data = {
                "id": i,
                "value": f"data_item_{i}",
                "producer_pid": os.getpid(),
                "timestamp": time.time()
            }
            
            print(f"Producer: Sending item {i}")
            
            # Process IPC error on item 7
            if i == 7:
                # Close connection unexpectedly - this creates an IPC error
                print("Producer: Simulating IPC failure...")
                conn_send.close()
                # Try to send after closing - this should raise an exception
                conn_send.send(data)  # This will fail
                
            conn_send.send(data)
            time.sleep(0.1)
        
        print("Producer: All data sent successfully")
        
    except Exception as e:
        print(f"🚨 Producer Exception: {e}")
        time.sleep(1)  # Give ThinkingSDK time to process
        raise
        
    finally:
        try:
            conn_send.close()
        except:
            pass
        print("Producer: Stopping ThinkingSDK...")
        thinking.stop()
        time.sleep(0.5)

def consumer_process(conn_recv):
    """Consumer process that receives data via pipe"""
    
    print(f"Consumer (PID: {os.getpid()}): Starting ThinkingSDK...")
    thinking.start(config_file="thinkingsdk.yaml")
    
    received_items = []
    
    try:
        print("Consumer: Starting data consumption...")
        
        timeout_count = 0
        max_timeouts = 3
        
        while timeout_count < max_timeouts:
            try:
                # Poll with timeout to detect communication issues
                if conn_recv.poll(timeout=2.0):
                    data = conn_recv.recv()
                    received_items.append(data)
                    print(f"Consumer: Received item {data['id']} from PID {data['producer_pid']}")
                    timeout_count = 0  # Reset timeout counter
                else:
                    timeout_count += 1
                    print(f"Consumer: Timeout {timeout_count}/{max_timeouts} waiting for data")
                    
                    if timeout_count >= max_timeouts:
                        raise TimeoutError("Consumer: Too many timeouts - producer may have crashed")
                        
            except EOFError as e:
                print("Consumer: Producer closed connection")
                break
            except Exception as e:
                print(f"🚨 Consumer: IPC Error - {e}")
                raise
        
        print(f"Consumer: Received {len(received_items)} items total")
        
        # Validate data integrity
        expected_items = list(range(7))  # We expect 0-6 before the IPC failure
        received_ids = [item['id'] for item in received_items]
        
        missing_items = set(expected_items) - set(received_ids)
        if missing_items:
            raise RuntimeError(f"Consumer: Data loss detected - missing items: {missing_items}")
            
    except Exception as e:
        print(f"🚨 Consumer Exception: {e}")
        time.sleep(1)  # Give ThinkingSDK time to process
        raise
        
    finally:
        try:
            conn_recv.close()
        except:
            pass
        print("Consumer: Stopping ThinkingSDK...")
        thinking.stop()
        time.sleep(0.5)

def network_worker_process(port):
    """Worker that communicates via network sockets"""
    
    print(f"NetworkWorker (PID: {os.getpid()}): Starting ThinkingSDK...")
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Create socket client
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        print(f"NetworkWorker: Connecting to localhost:{port}")
        sock.connect(('localhost', port))
        
        # Send some data
        for i in range(5):
            message = f"Message-{i} from PID-{os.getpid()}"
            sock.send(message.encode())
            
            response = sock.recv(1024)
            print(f"NetworkWorker: Sent '{message}', got response: {response.decode()}")
            time.sleep(0.2)
            
        sock.close()
        
    except Exception as e:
        print(f"🚨 NetworkWorker Exception: {e}")
        time.sleep(1)
        raise
        
    finally:
        print("NetworkWorker: Stopping ThinkingSDK...")
        thinking.stop()
        time.sleep(0.5)

def network_server_process(port):
    """Server process for network communication testing"""
    
    print(f"NetworkServer (PID: {os.getpid()}): Starting ThinkingSDK...")
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Create socket server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('localhost', port))
        server_sock.listen(1)
        server_sock.settimeout(10)  # 10 second timeout
        
        print(f"NetworkServer: Listening on port {port}")
        
        client_sock, addr = server_sock.accept()
        print(f"NetworkServer: Client connected from {addr}")
        
        # Handle client messages
        message_count = 0
        while message_count < 5:
            data = client_sock.recv(1024)
            if not data:
                break
                
            message = data.decode()
            print(f"NetworkServer: Received '{message}'")
            
            # Process server error on 3rd message
            if message_count == 2:
                print("NetworkServer: Simulating server error...")
                client_sock.close()
                raise ConnectionAbortedError("Server processing failure during processing")
            
            response = f"ACK-{message_count}"
            client_sock.send(response.encode())
            message_count += 1
        
        client_sock.close()
        server_sock.close()
        
    except Exception as e:
        print(f"🚨 NetworkServer Exception: {e}")
        time.sleep(1)
        raise
        
    finally:
        print("NetworkServer: Stopping ThinkingSDK...")
        thinking.stop()
        time.sleep(0.5)

def main():
    print("🚨 Starting multi-process communication scenario...")
    print(f"Main process PID: {os.getpid()}")
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Test 1: Pipe-based IPC
        print("\n=== Test 1: Pipe-based IPC ===")
        conn_send, conn_recv = multiprocessing.Pipe()
        
        producer = multiprocessing.Process(target=producer_process, args=(conn_send,))
        consumer = multiprocessing.Process(target=consumer_process, args=(conn_recv,))
        
        producer.start()
        consumer.start()
        
        producer.join(timeout=15)
        consumer.join(timeout=15)
        
        print(f"Producer exit code: {producer.exitcode}")
        print(f"Consumer exit code: {consumer.exitcode}")
        
        # Test 2: Network-based IPC
        print("\n=== Test 2: Network-based IPC ===")
        port = 9999
        
        server = multiprocessing.Process(target=network_server_process, args=(port,))
        server.start()
        time.sleep(1)  # Give server time to start
        
        client = multiprocessing.Process(target=network_worker_process, args=(port,))
        client.start()
        
        server.join(timeout=15)
        client.join(timeout=15)
        
        print(f"Server exit code: {server.exitcode}")
        print(f"Client exit code: {client.exitcode}")
        
    except Exception as e:
        print(f"🚨 Main process exception: {e}")
        time.sleep(2)
        raise
        
    finally:
        print("Main process: Stopping ThinkingSDK...")
        thinking.stop()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True) if sys.platform == 'win32' else None
    
    try:
        main()
        print("✅ Multi-process communication scenario completed!")
    except Exception as e:
        print(f"🚨 Multi-process communication scenario failed: {e}")
    
    print("Check ThinkingSDK server - events from different PIDs should be visible!")