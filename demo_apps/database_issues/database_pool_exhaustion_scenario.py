"""
Database connection pool exhaustion scenario.
Tests ThinkingSDK's ability to detect resource exhaustion patterns.
"""

import thinking_sdk_client as thinking
import threading
import time
import sqlite3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

thinking.start(config_file="thinkingsdk.yaml")

# Process connection pool with limited connections
MAX_CONNECTIONS = 5
connection_pool = []
pool_lock = threading.Lock()
active_connections = 0

def get_connection():
    """Process getting connection from pool"""
    global active_connections
    
    with pool_lock:
        if active_connections >= MAX_CONNECTIONS:
            # Pool exhausted - this should be detected by ThinkingSDK
            raise RuntimeError(f"Connection pool exhausted! Active: {active_connections}, Max: {MAX_CONNECTIONS}")
        
        active_connections += 1
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        connection_pool.append(conn)
        
        return conn

def release_connection(conn):
    """Release connection back to pool"""
    global active_connections
    
    with pool_lock:
        if conn in connection_pool:
            connection_pool.remove(conn)
            conn.close()
            active_connections -= 1

def database_worker(worker_id, hold_time=2.0):
    """Worker that holds database connection"""
    try:
        
        
        # Get connection from pool
        conn = get_connection()
        
        # Process database work
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS check_table (id INTEGER, data TEXT)")
        cursor.execute("INSERT INTO check_table VALUES (?, ?)", (worker_id, f"data_{worker_id}"))
        conn.commit()
        
        
        time.sleep(hold_time)  # Hold connection longer than needed
        
        # Query data
        cursor.execute("SELECT * FROM check_table WHERE id = ?", (worker_id,))
        result = cursor.fetchone()
        
        
        return f"Worker-{worker_id}: Success"
        
    except Exception as e:
        raise
        
    finally:
        if 'conn' in locals():
            release_connection(conn)

def process_n_plus_one_queries():
    """Process N+1 query problem"""
    try:
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("CREATE TABLE IF NOT EXISTS authors (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, author_id INTEGER)")
        
        # Insert test data
        authors = [("Author 1",), ("Author 2",), ("Author 3",)]
        cursor.executemany("INSERT INTO authors (name) VALUES (?)", authors)
        
        books = [
            ("Book A", 1), ("Book B", 1), ("Book C", 2), 
            ("Book D", 2), ("Book E", 3), ("Book F", 3)
        ]
        cursor.executemany("INSERT INTO books (title, author_id) VALUES (?, ?)", books)
        conn.commit()
        
        # N+1 Query Anti-pattern
        
        
        # Query 1: Get all authors
        cursor.execute("SELECT * FROM authors")
        authors = cursor.fetchall()
        
        
        # Query N: For each author, get their books (N additional queries)
        all_author_books = []
        for author in authors:
            author_id, author_name = author
            
            # This creates N additional queries - inefficient!
            cursor.execute("SELECT * FROM books WHERE author_id = ?", (author_id,))
            books = cursor.fetchall()
            
            all_author_books.append({
                "author": author_name,
                "books": books,
                "book_count": len(books)
            })
            
            
        
        
        
        # Better approach (commented for comparison):
        # cursor.execute("""
        #     SELECT a.name, b.title 
        #     FROM authors a 
        #     LEFT JOIN books b ON a.id = b.author_id
        #     ORDER BY a.name, b.title
        # """)
        
        return all_author_books
        
    except Exception as e:
        raise
        
    finally:
        if 'conn' in locals():
            release_connection(conn)

def main():
    
    try:
        # Test 1: Pool exhaustion with concurrent workers
        
        
        futures = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit more workers than available connections
            for i in range(8):  # 8 workers, but only 5 connections available
                hold_time = 3.0 if i < 6 else 1.0  # First 6 hold longer
                future = executor.submit(database_worker, i, hold_time)
                futures.append(future)
                time.sleep(0.2)  # Stagger the requests
            
            # Wait for completion
            completed_count = 0
            error_count = 0
            
            for future in as_completed(futures, timeout=15):
                try:
                    result = future.result()
                    completed_count += 1
                except Exception as e:
                    error_count += 1
        
        
        # Test 2: N+1 Query Problem
        
        author_books = process_n_plus_one_queries()
        
        
        # Test 3: Connection leak processing
        
        
        leaked_connections = []
        try:
            # Intentionally "leak" connections (get but don't release)
            for i in range(3):
                conn = get_connection()
                leaked_connections.append(conn)
                
            
            # Try to get more connections - should fail
            extra_conn = get_connection()
            
        except RuntimeError as e:
            
        finally:
            # Clean up leaked connections
            for i, conn in enumerate(leaked_connections):
                
                release_connection(conn)
        
    except Exception as e:
        time.sleep(2)  
        raise
    
    finally:
        # Cleanup any remaining connections
        
        for conn in connection_pool.copy():
            conn.close()
        connection_pool.clear()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
    finally:
        
        thinking.stop()