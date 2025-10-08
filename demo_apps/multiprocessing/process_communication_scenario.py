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
    
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        
        
        for i in range(10):
            data = {
                "id": i,
                "value": f"data_item_{i}",
                "producer_pid": os.getpid(),
                "timestamp": time.time()
            }
            
            
            
            # Process IPC error on item 7
            if i == 7:
                # Close connection unexpectedly - this creates an IPC error
                
                conn_send.close()
                # Try to send after closing - this should raise an exception
                conn_send.send(data)  # This will fail
                
            conn_send.send(data)
            time.sleep(0.1)
        
        
        
    except Exception as e:
        time.sleep(1)  
        raise
        
    finally:
        try:
            conn_send.close()
        except:
            pass
        
        thinking.stop()
        time.sleep(0.5)

def consumer_process(conn_recv):
    """Consumer process that receives data via pipe"""
    
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    received_items = []
    
    try:
        
        
        timeout_count = 0
        max_timeouts = 3
        
        while timeout_count < max_timeouts:
            try:
                # Poll with timeout to detect communication issues
                if conn_recv.poll(timeout=2.0):
                    data = conn_recv.recv()
                    received_items.append(data)
                    
                    timeout_count = 0  # Reset timeout counter
                else:
                    timeout_count += 1
                    
                    
                    if timeout_count >= max_timeouts:
                        raise TimeoutError("Consumer: Too many timeouts - producer may have crashed")
                        
            except EOFError as e:
                
                break
            except Exception as e:
                raise
        
        
        
        # Validate data integrity
        expected_items = list(range(7))  # We expect 0-6 before the IPC failure
        received_ids = [item['id'] for item in received_items]
        
        missing_items = set(expected_items) - set(received_ids)
        if missing_items:
            raise RuntimeError(f"Consumer: Data loss detected - missing items: {missing_items}")
            
    except Exception as e:
        time.sleep(1)  
        raise
        
    finally:
        try:
            conn_recv.close()
        except:
            pass
        
        thinking.stop()
        time.sleep(0.5)

def network_worker_process(port):
    """Worker that communicates via network sockets"""
    
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Create socket client
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        
        sock.connect(('localhost', port))
        
        # Send some data
        for i in range(5):
            message = f"Message-{i} from PID-{os.getpid()}"
            sock.send(message.encode())
            
            response = sock.recv(1024)
            
            time.sleep(0.2)
            
        sock.close()
        
    except Exception as e:
        time.sleep(1)
        raise
        
    finally:
        
        thinking.stop()
        time.sleep(0.5)

def network_server_process(port):
    """Server process for network communication testing"""
    
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Create socket server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(('localhost', port))
        server_sock.listen(1)
        server_sock.settimeout(10)  # 10 second timeout
        
        
        
        client_sock, addr = server_sock.accept()
        
        
        # Handle client messages
        message_count = 0
        while message_count < 5:
            data = client_sock.recv(1024)
            if not data:
                break
                
            message = data.decode()
            
            
            # Process server error on 3rd message
            if message_count == 2:
                
                client_sock.close()
                raise ConnectionAbortedError("Server processing failure during processing")
            
            response = f"ACK-{message_count}"
            client_sock.send(response.encode())
            message_count += 1
        
        client_sock.close()
        server_sock.close()
        
    except Exception as e:
        time.sleep(1)
        raise
        
    finally:
        
        thinking.stop()
        time.sleep(0.5)

def main():
    
    
    thinking.start(config_file="thinkingsdk.yaml")
    
    try:
        # Test 1: Pipe-based IPC
        
        conn_send, conn_recv = multiprocessing.Pipe()
        
        producer = multiprocessing.Process(target=producer_process, args=(conn_send,))
        consumer = multiprocessing.Process(target=consumer_process, args=(conn_recv,))
        
        producer.start()
        consumer.start()
        
        producer.join(timeout=15)
        consumer.join(timeout=15)
        
        
        
        
        # Test 2: Network-based IPC
        
        port = 9999
        
        server = multiprocessing.Process(target=network_server_process, args=(port,))
        server.start()
        time.sleep(1)  # Give server time to start
        
        client = multiprocessing.Process(target=network_worker_process, args=(port,))
        client.start()
        
        server.join(timeout=15)
        client.join(timeout=15)
        
        
        
        
    except Exception as e:
        time.sleep(2)
        raise
        
    finally:
        
        thinking.stop()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True) if sys.platform == 'win32' else None
    
    try:
        main()
    except Exception as e:
    