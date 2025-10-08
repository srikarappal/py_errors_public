"""
Security vulnerabilities scenario.
Tests common security issues that ThinkingSDK should help detect.
"""

import thinking_sdk_client as thinking
import hashlib
import sqlite3
import os
import tempfile
import json
import base64
import time
import random
import string

thinking.start(config_file="thinkingsdk.yaml")

class InsecureUserManager:
    """User management with security vulnerabilities"""
    
    def __init__(self):
        # Create in-memory database for testing
        self.conn = sqlite3.connect(":memory:")
        self.setup_database()
        
    def setup_database(self):
        """Setup database tables"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def create_user_insecure(self, username: str, password: str, email: str) -> dict:
        """Create user with insecure password storage"""
        cursor = self.conn.cursor()
        
        
        try:
            # Security vulnerability 1: Store password in plaintext
            cursor.execute("""
                INSERT INTO users (username, password, email) 
                VALUES (?, ?, ?)
            """, (username, password, email))  # Password stored as plaintext!
            
            user_id = cursor.lastrowid
            self.conn.commit()
            
            
            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'password_storage': 'plaintext'  # This is a red flag!
            }
            
        except sqlite3.IntegrityError as e:
            raise ValueError(f"User creation failed: {e}")
    
    def create_user_weak_hash(self, username: str, password: str, email: str) -> dict:
        """Create user with weak password hashing"""
        cursor = self.conn.cursor()
        
        
        try:
            # Security vulnerability 2: Use weak MD5 hash
            weak_hash = hashlib.md5(password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (username, password, email) 
                VALUES (?, ?, ?)
            """, (username, weak_hash, email))
            
            user_id = cursor.lastrowid
            self.conn.commit()
            
            
            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'password_storage': 'md5_hash'  # Still weak!
            }
            
        except sqlite3.IntegrityError as e:
            raise ValueError(f"User creation failed: {e}")
    
    def authenticate_user_sql_injection(self, username: str, password: str) -> dict:
        """Authenticate user with SQL injection vulnerability"""
        cursor = self.conn.cursor()
        
        
        # Security vulnerability 3: SQL injection via string formatting
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        
        
        try:
            cursor.execute(query)  # This is vulnerable to SQL injection!
            user = cursor.fetchone()
            
            if user:
                
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'authenticated': True,
                    'method': 'sql_injection_vulnerable'
                }
            else:
                return {'authenticated': False}
                
        except sqlite3.Error as e:
            
            raise
    
    def create_session_insecure(self, user_id: int) -> str:
        """Create session with security vulnerabilities"""
        
        # Security vulnerability 4: Predictable session ID
        session_id = f"session_{user_id}_{int(time.time())}"  # Easily guessable!
        
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id) 
            VALUES (?, ?)
        """, (session_id, user_id))
        
        self.conn.commit()
        
        return session_id

class InsecureFileManager:
    """File management with security vulnerabilities"""
    
    def __init__(self):
        self.upload_dir = tempfile.mkdtemp()
    
    def save_file_insecure(self, filename: str, content: bytes) -> str:
        """Save file with path traversal vulnerability"""
        
        
        # Security vulnerability 5: No path sanitization
        file_path = os.path.join(self.upload_dir, filename)  # Vulnerable to ../../../etc/passwd
        
        
        # Check if path traversal was attempted
        if ".." in filename or filename.startswith("/"):
            raise SecurityError(f"Path traversal attack attempted: {filename}")
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return file_path
            
        except Exception as e:
            raise
    
    def read_file_insecure(self, filename: str) -> bytes:
        """Read file with directory traversal vulnerability"""
        
        
        
        # Security vulnerability 6: Direct file access without validation
        file_path = os.path.join(self.upload_dir, filename)
        
        if not file_path.startswith(self.upload_dir):
            raise SecurityError(f"Directory traversal attack: {filename}")
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            return content
            
        except FileNotFoundError:
            raise ValueError(f"File not found: {filename}")

class SecurityError(Exception):
    """Custom security error"""
    pass

def check_password_security_vulnerabilities():
    """Test password-related security vulnerabilities"""
    
    user_manager = InsecureUserManager()
    
    # Test 1: Plaintext password storage
    try:
        user1 = user_manager.create_user_insecure("admin", "admin123", "admin@example.com")
        
    except Exception as e:
        
    
    # Test 2: Weak password hashing
    try:
        user2 = user_manager.create_user_weak_hash("user", "password", "user@example.com") 
        
    except Exception as e:
        

def check_sql_injection_vulnerabilities():
    """Test SQL injection vulnerabilities"""
    
    user_manager = InsecureUserManager()
    
    # Setup test user
    user_manager.create_user_insecure("testuser", "testpass", "test@example.com")
    
    # Test 3: SQL injection attack
    try:
        # Attempt SQL injection
        malicious_username = "admin' OR '1'='1"
        malicious_password = "anything"
        
        
        result = user_manager.authenticate_user_sql_injection(malicious_username, malicious_password)
        
        if result.get('authenticated'):
            raise SecurityError("SQL injection vulnerability exploited")
        else:
            
    except sqlite3.Error as e:
        raise SecurityError(f"SQL injection vulnerability: {e}")
    
    except Exception as e:
        
        raise

def check_session_security_vulnerabilities():
    """Test session management security vulnerabilities"""
    
    user_manager = InsecureUserManager()
    
    # Test 4: Predictable session IDs
    try:
        # Create multiple sessions to show predictable pattern
        session_ids = []
        
        for user_id in range(1, 4):
            session_id = user_manager.create_session_insecure(user_id)
            session_ids.append(session_id)
            
        
        
        
        # Check if sessions are predictable
        if all("session_" in sid for sid in session_ids):
            raise SecurityError("Session IDs are predictable and can be guessed by attackers")
            
    except Exception as e:
        
        raise

def check_file_security_vulnerabilities():
    """Test file handling security vulnerabilities"""
    
    file_manager = InsecureFileManager()
    
    # Test 5: Path traversal attack
    try:
        # Attempt path traversal
        malicious_filename = "../../../etc/passwd"
        check_content = b"malicious content"
        
        
        file_path = file_manager.save_file_insecure(malicious_filename, check_content)
        
    except SecurityError as e:
        
    except Exception as e:
        raise SecurityError(f"Path traversal vulnerability: {e}")
    
    # Test 6: Directory traversal in file reading
    try:
        # First save a legitimate file
        safe_filename = "test.txt"
        file_manager.save_file_insecure(safe_filename, b"safe content")
        
        # Try to read with directory traversal
        malicious_read = "../../../etc/passwd"
        content = file_manager.read_file_insecure(malicious_read)
        
        
    except SecurityError as e:
        
    except Exception as e:
        raise SecurityError(f"Directory traversal vulnerability: {e}")

def check_data_exposure_in_logs():
    """Test sensitive data exposure in logs"""
    
    # Test 7: Logging sensitive information
    try:
        # Process logging sensitive data (anti-pattern)
        credit_card = "4532-1234-5678-9012"
        ssn = "123-45-6789"
        password = "user_secret_password"
        
          # Credit card in logs!
          # SSN in logs!
          # Password in logs!
        
        # This should be detected as a security vulnerability
        raise SecurityError("Sensitive data (credit card, SSN, password) logged in plaintext")
        
    except SecurityError as e:
        raise
    
    except Exception as e:
        
        raise

def main():
    
    vulnerability_tests = [
        ("Password Security", check_password_security_vulnerabilities),
        ("SQL Injection", check_sql_injection_vulnerabilities),
        ("Session Security", check_session_security_vulnerabilities),
        ("File Security", check_file_security_vulnerabilities),
        ("Data Exposure", check_data_exposure_in_logs)
    ]
    
    vulnerabilities_detected = []
    
    try:
        for check_name, check_func in vulnerability_tests:
            
            
            try:
                check_func()
                
            except SecurityError as e:
                vulnerabilities_detected.append((check_name, str(e)))
                
            except Exception as e:
                vulnerabilities_detected.append((check_name, f"Error: {e}"))
        
        # Summary
        
        
        
        if vulnerabilities_detected:
            for vuln_name, vuln_desc in vulnerabilities_detected:
                
            
            # Raise summary exception
            vuln_summary = "; ".join([f"{name}: {desc}" for name, desc in vulnerabilities_detected])
            raise SecurityError(f"Multiple security vulnerabilities detected: {vuln_summary}")
        
        
    except Exception as e:
        time.sleep(2)
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
    finally:
        
        thinking.stop()