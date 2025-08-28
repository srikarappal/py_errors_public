"""
Mock GitHub integration for testing ThinkingSDK without real GitHub App.

Uses Personal Access Token for testing the complete end-to-end flow:
Runtime Exception → GitHub Issue → Sandbox Analysis → PR Creation
"""

import os
import time
import base64
import aiohttp
import asyncio
import tempfile
import zipfile
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class MockGitHubAuth:
    """Mock GitHub authentication using Personal Access Token."""
    
    def __init__(self, personal_access_token: str):
        """
        Initialize with Personal Access Token for testing.
        
        Args:
            personal_access_token: GitHub PAT with repo permissions
        """
        self.token = personal_access_token
        self.session = None
        
    async def setup(self):
        """Setup HTTP session."""
        self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Cleanup HTTP session."""
        if self.session:
            await self.session.close()
    
    async def get_installation_access_token(self, installation_id: str) -> str:
        """Mock installation token - just return the PAT."""
        return self.token


class MockGitHubRepositoryAccess:
    """Mock repository operations using GitHub API with PAT."""
    
    def __init__(self, auth: MockGitHubAuth):
        """Initialize with mock GitHub authentication."""
        self.auth = auth
        
    async def get_repository_info(self, installation_id: str, repo_full_name: str) -> Dict[str, Any]:
        """Get repository information."""
        headers = {
            'Authorization': f'token {self.auth.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ThinkingSDK-Test/1.0'
        }
        
        url = f"https://api.github.com/repos/{repo_full_name}"
        
        async with self.auth.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get repo info: {response.status} - {error_text}")
    
    async def get_file_content(self, installation_id: str, repo_full_name: str, 
                              file_path: str, ref: str = "main") -> Optional[str]:
        """Get file content from repository."""
        headers = {
            'Authorization': f'token {self.auth.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ThinkingSDK-Test/1.0'
        }
        
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
        params = {'ref': ref}
        
        async with self.auth.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data['type'] == 'file':
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content
            return None
    
    async def download_repository_archive(self, installation_id: str, repo_full_name: str, 
                                        ref: str = "main") -> bytes:
        """Download entire repository as ZIP archive."""
        headers = {
            'Authorization': f'token {self.auth.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ThinkingSDK-Test/1.0'
        }
        
        url = f"https://api.github.com/repos/{repo_full_name}/zipball/{ref}"
        
        async with self.auth.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to download repository: {response.status}")
    
    async def create_issue(self, installation_id: str, repo_full_name: str, 
                          issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitHub issue."""
        headers = {
            'Authorization': f'token {self.auth.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ThinkingSDK-Test/1.0'
        }
        
        url = f"https://api.github.com/repos/{repo_full_name}/issues"
        
        async with self.auth.session.post(url, headers=headers, json=issue_data) as response:
            if response.status == 201:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create issue: {response.status} - {error_text}")
    
    async def create_pull_request(self, installation_id: str, repo_full_name: str,
                                 pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create pull request."""
        headers = {
            'Authorization': f'token {self.auth.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ThinkingSDK-Test/1.0'
        }
        
        url = f"https://api.github.com/repos/{repo_full_name}/pulls"
        
        async with self.auth.session.post(url, headers=headers, json=pr_data) as response:
            if response.status == 201:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Failed to create PR: {response.status} - {error_text}")


class MockGitHubIntegrationManager:
    """Mock version of GitHubIntegrationManager for testing."""
    
    def __init__(self, db, personal_access_token: str):
        """Initialize with database and PAT for testing."""
        self.db = db
        self.github_auth = MockGitHubAuth(personal_access_token)
        self.repo_access = MockGitHubRepositoryAccess(self.github_auth)
        
        # Import sandbox components
        from thinking_sdk_server.sandbox_environment import RepositoryCloner, EnvironmentSetup, DebugProcess
        self.cloner = RepositoryCloner()
        self.env_setup = EnvironmentSetup()
        self.debug_process = DebugProcess(self.repo_access, self.cloner, self.env_setup)
    
    async def setup(self):
        """Setup mock GitHub integration."""
        await self.github_auth.setup()
    
    async def cleanup(self):
        """Cleanup mock GitHub integration."""
        await self.github_auth.cleanup()
    
    async def process_runtime_failure(self, organization_id: str, 
                                    exception_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock version of complete runtime failure processing.
        """
        start_time = time.time()
        
        try:
            # Get GitHub configuration (mock values for testing)
            github_config = {
                'installation_id': 'mock_installation_123',
                'repo_full_name': os.getenv('TEST_GITHUB_REPO', 'user/test-repo'),
                'default_branch': 'main'
            }
            
            # Create GitHub issue with rich runtime context
            issue_data = self._create_github_issue_data(exception_data)
            
            try:
                issue = await self.repo_access.create_issue(
                    github_config['installation_id'],
                    github_config['repo_full_name'], 
                    issue_data
                )
                issue_url = issue['html_url']
                
                print(f"✅ Created GitHub issue: {issue_url}")
                
            except Exception as e:
                print(f"⚠️  Failed to create GitHub issue: {e}")
                issue_url = f"https://github.com/{github_config['repo_full_name']}/issues/mock"
            
            # Run complete debug process in sandbox
            print("🔄 Starting comprehensive debug process...")
            debug_results = await self.debug_process.run_complete_debug_process(
                exception_data, github_config
            )
            
            # Create PR with fix (mock for now)
            pr_url = await self._create_mock_pr(github_config, debug_results, exception_data)
            
            processing_time = time.time() - start_time
            
            return {
                'status': 'success',
                'issue_url': issue_url,
                'pr_url': pr_url,
                'debug_results': debug_results,
                'processing_time': processing_time,
                'github_config': github_config
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _create_github_issue_data(self, exception_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitHub issue data with rich runtime context."""
        exception_info = exception_data.get('exception', {})
        
        title = f"🚨 Runtime Error: {exception_info.get('type', 'Unknown')} in {exception_data.get('func', 'unknown function')}"
        
        body = f"""## 🔍 Runtime Failure Detected by ThinkingSDK

### Error Details
- **Exception**: {exception_info.get('type', 'Unknown')}: {exception_info.get('message', 'No message')}
- **File**: {exception_data.get('file_path', 'unknown')}:{exception_data.get('line', 'unknown')}
- **Function**: {exception_data.get('func', 'unknown')}
- **Timestamp**: {datetime.fromtimestamp(exception_data.get('ts', time.time())).isoformat()}

### Runtime Context (Unique to ThinkingSDK!)
- **Severity**: {exception_data.get('severity', 'unknown')}
- **Business Impact**: {exception_data.get('business_impact', 'unknown')}
- **Fix Urgency**: {exception_data.get('fix_urgency', 'unknown')}
- **Local Variables**: 
```json
{exception_data.get('locals', {})}
```

### Traceback
```
{chr(10).join(exception_info.get('traceback_summary', ['No traceback available']))}
```

### Process Status
🔄 ThinkingSDK is analyzing this failure and will create a fix PR shortly...

**ETA: 3-20 minutes** (depending on repository complexity and test suite size)

---
🤖 Automatically created by ThinkingSDK runtime monitoring
"""
        
        return {
            "title": title,
            "body": body,
            "labels": [
                "thinkingsdk-auto", 
                "bug", 
                "runtime-failure",
                f"severity-{exception_data.get('severity', 'unknown')}",
                f"urgency-{exception_data.get('fix_urgency', 'normal')}"
            ]
        }
    
    async def _create_mock_pr(self, github_config: Dict[str, Any], 
                            debug_results: Dict[str, Any], 
                            exception_data: Dict[str, Any]) -> str:
        """Create mock PR or real PR if debug was successful."""
        
        if debug_results.get('success'):
            # Create actual PR with fix
            pr_data = {
                "title": f"🤖 Fix {exception_data.get('exception', {}).get('type')} runtime error",
                "body": self._generate_pr_description(debug_results, exception_data),
                "head": f"thinkingsdk-fix-{int(time.time())}",
                "base": github_config.get('default_branch', 'main')
            }
            
            try:
                pr = await self.repo_access.create_pull_request(
                    github_config['installation_id'],
                    github_config['repo_full_name'],
                    pr_data
                )
                print(f"✅ Created GitHub PR: {pr['html_url']}")
                return pr['html_url']
                
            except Exception as e:
                print(f"⚠️  Failed to create PR: {e}")
                return f"https://github.com/{github_config['repo_full_name']}/pulls/mock"
        
        else:
            print("❌ Debug process failed - no PR created")
            return f"https://github.com/{github_config['repo_full_name']}/pulls/failed"
    
    def _generate_pr_description(self, debug_results: Dict[str, Any], 
                               exception_data: Dict[str, Any]) -> str:
        """Generate comprehensive PR description."""
        steps = debug_results.get("process_steps", {})
        
        return f"""## 🤖 ThinkingSDK Automated Fix

### Runtime Failure Analysis
- **Error**: {exception_data.get('exception', {}).get('type')}: {exception_data.get('exception', {}).get('message')}
- **Processing Time**: {debug_results.get('total_time', 0):.1f} seconds
- **Severity**: {exception_data.get('severity', 'unknown')}
- **Business Impact**: {exception_data.get('business_impact', 'unknown')}

### 🔍 Debug Process Results
- **✅ Files Located**: {steps.get('a_locate_files', {}).get('success', False)} ({steps.get('a_locate_files', {}).get('execution_time', 0):.1f}s)
- **✅ Error Reproduced**: {steps.get('b_replicate_error', {}).get('error_reproduced', False)} ({steps.get('b_replicate_error', {}).get('execution_time', 0):.1f}s)
- **✅ Fix Applied**: {steps.get('c_make_change', {}).get('success', False)} ({steps.get('c_make_change', {}).get('execution_time', 0):.1f}s)
- **✅ Unit Tests**: {steps.get('d_unit_tests', {}).get('test_passed', False)} ({steps.get('d_unit_tests', {}).get('execution_time', 0):.1f}s)
- **✅ Full Test Suite**: {steps.get('e_full_tests', {}).get('all_tests_passed', False)} ({steps.get('e_full_tests', {}).get('execution_time', 0):.1f}s)
- **✅ Integration Verified**: {steps.get('f_integration_test', {}).get('success', False)} ({steps.get('f_integration_test', {}).get('execution_time', 0):.1f}s)

### 📁 Files Changed
{self._format_changed_files(steps)}

### 🧪 Tests Added
{self._format_test_files(steps)}

### 💡 Runtime Context Used
```json
{{"locals": {exception_data.get('locals', {})}, "business_context": "{exception_data.get('business_impact', 'medium')} impact"}}
```

### 🔧 Fix Details
{self._format_fix_details(steps)}

---
🤖 **Generated by ThinkingSDK with complete environment replication and testing**

**Confidence Level**: {self._calculate_fix_confidence(debug_results)}

**⚠️ Please review carefully before merging!**

**Collaboration Welcome**: 
- @copilot please review error handling patterns
- @claude-code please optimize for readability
- @thinkingsdk-bot available for questions about runtime analysis
"""
    
    def _format_changed_files(self, steps: Dict[str, Any]) -> str:
        """Format list of changed files."""
        changed_files = []
        
        if steps.get('c_make_change', {}).get('fixed_file'):
            changed_files.append(f"- 🔧 {steps['c_make_change']['fixed_file']}")
        
        return '\n'.join(changed_files) if changed_files else "- No files changed"
    
    def _format_test_files(self, steps: Dict[str, Any]) -> str:
        """Format list of test files."""
        test_files = []
        
        if steps.get('d_unit_tests', {}).get('test_file'):
            test_files.append(f"- 🧪 tests/{steps['d_unit_tests']['test_file']}")
        
        return '\n'.join(test_files) if test_files else "- No tests added"
    
    def _format_fix_details(self, steps: Dict[str, Any]) -> str:
        """Format fix implementation details."""
        fix_details = []
        
        locate_step = steps.get('a_locate_files', {})
        if locate_step.get('primary_file'):
            fix_details.append(f"**Primary File**: {locate_step['primary_file'].get('path', 'unknown')}")
            fix_details.append(f"**Function**: {locate_step['primary_file'].get('function', 'unknown')}")
            fix_details.append(f"**Line**: {locate_step['primary_file'].get('line', 'unknown')}")
        
        repro_step = steps.get('b_replicate_error', {})
        if repro_step.get('error_reproduced'):
            fix_details.append("**Error Reproduction**: ✅ Successfully reproduced original error")
        else:
            fix_details.append("**Error Reproduction**: ❌ Could not reproduce original error")
        
        return '\n'.join(fix_details) if fix_details else "No fix details available"
    
    def _calculate_fix_confidence(self, debug_results: Dict[str, Any]) -> str:
        """Calculate confidence level based on debug process results."""
        steps = debug_results.get("process_steps", {})
        
        confidence_score = 0
        max_score = 6
        
        if steps.get('a_locate_files', {}).get('success'):
            confidence_score += 1
        if steps.get('b_replicate_error', {}).get('error_reproduced'):
            confidence_score += 2  # Error reproduction is very important
        if steps.get('c_make_change', {}).get('success'):
            confidence_score += 1
        if steps.get('d_unit_tests', {}).get('test_passed'):
            confidence_score += 1
        if steps.get('e_full_tests', {}).get('all_tests_passed'):
            confidence_score += 1
        
        confidence_percentage = (confidence_score / max_score) * 100
        
        if confidence_percentage >= 80:
            return f"🟢 High ({confidence_percentage:.0f}%)"
        elif confidence_percentage >= 60:
            return f"🟡 Medium ({confidence_percentage:.0f}%)"
        else:
            return f"🔴 Low ({confidence_percentage:.0f}%)"


# Environment configuration for testing
def get_mock_github_config() -> Dict[str, str]:
    """Get mock GitHub configuration for testing."""
    return {
        'personal_access_token': os.getenv('GITHUB_TEST_TOKEN', ''),
        'test_repository': os.getenv('TEST_GITHUB_REPO', 'user/test-repo'),
        'webhook_secret': os.getenv('GITHUB_WEBHOOK_SECRET', 'test_secret')
    }


def create_mock_github_manager(db) -> MockGitHubIntegrationManager:
    """Create mock GitHub integration manager for testing."""
    config = get_mock_github_config()
    
    if not config['personal_access_token']:
        raise Exception("GITHUB_TEST_TOKEN environment variable required for testing")
    
    return MockGitHubIntegrationManager(db, config['personal_access_token'])


# Test data generators
class TestCaseGenerator:
    """Generates realistic test cases for different production failure scenarios."""
    
    @staticmethod
    def generate_payment_processing_error() -> Dict[str, Any]:
        """Test Case 1: Payment processing ValueError."""
        return {
            "ts": time.time(),
            "pid": 12345,
            "thread": "MainThread",
            "event": "exception",
            "func": "process_payment",
            "file": "payment_service.py",
            "file_path": "/app/src/payment_service.py",
            "line": 45,
            "exception": {
                "type": "ValueError",
                "message": "invalid literal for int() with base 10: 'credit_card'",
                "structured_traceback": [
                    {
                        "file": "/app/src/payment_service.py",
                        "line": 45,
                        "func": "process_payment",
                        "code": "return int(payment_method)"
                    }
                ]
            },
            "locals": {
                "amount": 299.99,
                "payment_method": "credit_card",
                "user_id": 12345,
                "order_id": "ORD_2025_001"
            },
            "context": {
                "user_tier": "premium",
                "cart_value": 299.99,
                "session_id": "sess_abc123"
            },
            "severity": "critical",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "immediate"
        }
    
    @staticmethod
    def generate_database_keyerror() -> Dict[str, Any]:
        """Test Case 2: Database connection KeyError."""
        return {
            "ts": time.time(),
            "pid": 12346,
            "thread": "WorkerThread-1", 
            "event": "exception",
            "func": "get_user_orders",
            "file": "database.py",
            "file_path": "/app/src/database.py",
            "line": 78,
            "exception": {
                "type": "KeyError",
                "message": "'connection'",
                "structured_traceback": [
                    {
                        "file": "/app/src/database.py",
                        "line": 78,
                        "func": "get_user_orders",
                        "code": "conn = db_pool['connection']"
                    }
                ]
            },
            "locals": {
                "user_id": 67890,
                "db_pool": {"size": 0, "active": 0},
                "retry_count": 3
            },
            "context": {
                "database_status": "connection_pool_exhausted",
                "active_connections": 50,
                "max_connections": 50
            },
            "severity": "critical",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "immediate"
        }
    
    @staticmethod
    def generate_auth_attributeerror() -> Dict[str, Any]:
        """Test Case 3: Authentication AttributeError."""
        return {
            "ts": time.time(),
            "pid": 12347,
            "thread": "RequestThread-5",
            "event": "exception", 
            "func": "validate_user_session",
            "file": "auth_service.py",
            "file_path": "/app/src/auth_service.py",
            "line": 23,
            "exception": {
                "type": "AttributeError",
                "message": "'NoneType' object has no attribute 'is_authenticated'",
                "structured_traceback": [
                    {
                        "file": "/app/src/auth_service.py",
                        "line": 23,
                        "func": "validate_user_session",
                        "code": "return request.user.is_authenticated"
                    }
                ]
            },
            "locals": {
                "request": {"method": "POST", "path": "/api/secure-endpoint"},
                "session_token": "expired_token_xyz"
            },
            "context": {
                "endpoint": "/api/secure-endpoint",
                "security_level": "high",
                "user_role": "admin"
            },
            "severity": "high",
            "business_impact": "high", 
            "priority": "ALWAYS",
            "fix_urgency": "urgent"
        }
    
    @staticmethod
    def generate_api_indexerror() -> Dict[str, Any]:
        """Test Case 4: External API IndexError."""
        return {
            "ts": time.time(),
            "pid": 12348,
            "thread": "APIWorker-2",
            "event": "exception",
            "func": "process_external_api_response", 
            "file": "api_client.py",
            "file_path": "/app/src/api_client.py",
            "line": 156,
            "exception": {
                "type": "IndexError",
                "message": "list index out of range",
                "structured_traceback": [
                    {
                        "file": "/app/src/api_client.py",
                        "line": 156,
                        "func": "process_external_api_response",
                        "code": "return response['data']['results'][0]['value']"
                    }
                ]
            },
            "locals": {
                "response": {"status": "error", "data": {"results": []}},
                "api_provider": "stripe",
                "retry_attempt": 2
            },
            "context": {
                "api_endpoint": "https://api.stripe.com/v1/charges",
                "rate_limit_remaining": 0,
                "api_status": "degraded"
            },
            "severity": "high",
            "business_impact": "high",
            "priority": "ALWAYS", 
            "fix_urgency": "urgent"
        }

    # === CATEGORY 1: PAYMENT & E-COMMERCE (3 scenarios) ===
    
    @staticmethod
    def generate_payment_timeout_error() -> Dict[str, Any]:
        """Payment gateway timeout causing order failure."""
        return {
            "ts": time.time(),
            "pid": 12349,
            "thread": "PaymentWorker-3",
            "event": "exception",
            "func": "charge_credit_card",
            "file": "payment_gateway.py",
            "file_path": "/app/src/payment_gateway.py",
            "line": 89,
            "exception": {
                "type": "TimeoutError",
                "message": "Stripe API call timed out after 30 seconds",
                "structured_traceback": [
                    {
                        "file": "/app/src/payment_gateway.py",
                        "line": 89,
                        "func": "charge_credit_card",
                        "code": "response = await stripe_client.charges.create(timeout=30)"
                    }
                ]
            },
            "locals": {
                "amount_cents": 29999,
                "customer_id": "cus_abc123",
                "payment_method": "pm_card_visa",
                "retry_count": 2
            },
            "context": {
                "payment_gateway": "stripe",
                "gateway_status": "degraded",
                "order_value": 299.99,
                "customer_tier": "premium"
            },
            "severity": "critical",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "immediate"
        }
    
    @staticmethod
    def generate_inventory_concurrency_error() -> Dict[str, Any]:
        """Race condition in inventory management during high traffic."""
        return {
            "ts": time.time(),
            "pid": 12350,
            "thread": "InventoryWorker-7",
            "event": "exception",
            "func": "reserve_inventory",
            "file": "inventory_service.py",
            "file_path": "/app/src/inventory_service.py",
            "line": 156,
            "exception": {
                "type": "IntegrityError",
                "message": "UNIQUE constraint failed: inventory_reservations.product_id",
                "structured_traceback": [
                    {
                        "file": "/app/src/inventory_service.py",
                        "line": 156,
                        "func": "reserve_inventory",
                        "code": "await db.execute('INSERT INTO inventory_reservations ...')"
                    }
                ]
            },
            "locals": {
                "product_id": "prod_123",
                "quantity": 5,
                "available_stock": 2,
                "concurrent_requests": 12
            },
            "context": {
                "product_name": "Limited Edition iPhone",
                "flash_sale_active": True,
                "concurrent_users": 1247,
                "stock_level": "critically_low"
            },
            "severity": "critical",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "immediate"
        }

    # === CATEGORY 2: DATABASE & INFRASTRUCTURE (3 scenarios) ===
    
    @staticmethod
    def generate_connection_pool_exhaustion() -> Dict[str, Any]:
        """Database connection pool exhausted under load."""
        return {
            "ts": time.time(),
            "pid": 12351,
            "thread": "WebWorker-15",
            "event": "exception",
            "func": "get_user_profile",
            "file": "database_manager.py",
            "file_path": "/app/src/database_manager.py",
            "line": 45,
            "exception": {
                "type": "ConnectionError",
                "message": "QueuePool limit of size 20 overflow 10 reached, connection timed out",
                "structured_traceback": [
                    {
                        "file": "/app/src/database_manager.py",
                        "line": 45,
                        "func": "get_user_profile",
                        "code": "conn = await db_pool.acquire()"
                    }
                ]
            },
            "locals": {
                "user_id": 98765,
                "pool_size": 20,
                "active_connections": 30,
                "queue_length": 45
            },
            "context": {
                "load_level": "extreme",
                "concurrent_requests": 2341,
                "database_cpu": 89.5,
                "connection_wait_time": "45.2s"
            },
            "severity": "critical",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "immediate"
        }
    
    @staticmethod
    def generate_deadlock_detection_error() -> Dict[str, Any]:
        """Database deadlock during transaction processing."""
        return {
            "ts": time.time(),
            "pid": 12352,
            "thread": "TransactionWorker-4",
            "event": "exception",
            "func": "transfer_funds",
            "file": "transaction_service.py",
            "file_path": "/app/src/transaction_service.py",
            "line": 203,
            "exception": {
                "type": "DeadlockError",
                "message": "Transaction deadlock detected and automatically rolled back",
                "structured_traceback": [
                    {
                        "file": "/app/src/transaction_service.py",
                        "line": 203,
                        "func": "transfer_funds",
                        "code": "await db.execute('UPDATE accounts SET balance = balance - %s WHERE id = %s', amount, from_account)"
                    }
                ]
            },
            "locals": {
                "from_account": 1001,
                "to_account": 1002,
                "amount": 1500.00,
                "transaction_id": "txn_def456",
                "retry_count": 0
            },
            "context": {
                "transaction_type": "fund_transfer",
                "high_volume_period": True,
                "concurrent_transactions": 89,
                "lock_wait_timeout": "50s"
            },
            "severity": "high",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "urgent"
        }

    # === CATEGORY 3: AUTHENTICATION & SECURITY (2 scenarios) ===
    
    @staticmethod
    def generate_jwt_expiration_error() -> Dict[str, Any]:
        """JWT token expiration causing authentication failure."""
        return {
            "ts": time.time(),
            "pid": 12353,
            "thread": "AuthWorker-2",
            "event": "exception",
            "func": "validate_jwt_token",
            "file": "auth_middleware.py",
            "file_path": "/app/src/auth_middleware.py",
            "line": 67,
            "exception": {
                "type": "ExpiredSignatureError",
                "message": "Signature has expired",
                "structured_traceback": [
                    {
                        "file": "/app/src/auth_middleware.py",
                        "line": 67,
                        "func": "validate_jwt_token",
                        "code": "payload = jwt.decode(token, secret_key, algorithms=['HS256'])"
                    }
                ]
            },
            "locals": {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "user_id": 54321,
                "token_issued_at": 1692123456,
                "current_time": 1692210000
            },
            "context": {
                "endpoint": "/api/user/profile",
                "user_role": "admin",
                "session_duration": "24h",
                "auto_refresh_failed": True
            },
            "severity": "high",
            "business_impact": "medium",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }

    # === CATEGORY 4: EXTERNAL API INTEGRATIONS (3 scenarios) ===
    
    @staticmethod
    def generate_rate_limit_exceeded_error() -> Dict[str, Any]:
        """External API rate limit exceeded."""
        return {
            "ts": time.time(),
            "pid": 12354,
            "thread": "APIWorker-8",
            "event": "exception",
            "func": "fetch_user_data",
            "file": "external_api.py",
            "file_path": "/app/src/external_api.py",
            "line": 134,
            "exception": {
                "type": "RateLimitError",
                "message": "Rate limit exceeded: 429 Too Many Requests",
                "structured_traceback": [
                    {
                        "file": "/app/src/external_api.py",
                        "line": 134,
                        "func": "fetch_user_data",
                        "code": "response = await http_client.get(f'{api_base}/users/{user_id}')"
                    }
                ]
            },
            "locals": {
                "user_id": 78901,
                "api_provider": "facebook_graph_api",
                "requests_this_hour": 5000,
                "rate_limit": 4800,
                "retry_after": 3600
            },
            "context": {
                "api_endpoint": "https://graph.facebook.com/v18.0/me",
                "business_feature": "social_login",
                "peak_traffic_hour": True,
                "fallback_available": False
            },
            "severity": "high",
            "business_impact": "medium",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }
    
    @staticmethod
    def generate_webhook_processing_error() -> Dict[str, Any]:
        """Webhook payload processing failure."""
        return {
            "ts": time.time(),
            "pid": 12355,
            "thread": "WebhookWorker-1",
            "event": "exception",
            "func": "process_stripe_webhook",
            "file": "webhook_handlers.py",
            "file_path": "/app/src/webhook_handlers.py",
            "line": 78,
            "exception": {
                "type": "KeyError",
                "message": "'payment_intent'",
                "structured_traceback": [
                    {
                        "file": "/app/src/webhook_handlers.py",
                        "line": 78,
                        "func": "process_stripe_webhook",
                        "code": "payment_intent_id = payload['data']['object']['payment_intent']['id']"
                    }
                ]
            },
            "locals": {
                "event_type": "invoice.payment_succeeded",
                "payload": {"data": {"object": {"id": "in_abc123"}}},
                "stripe_signature": "v1=signature123",
                "webhook_source": "stripe"
            },
            "context": {
                "webhook_endpoint": "/webhooks/stripe",
                "payload_size": 2048,
                "processing_time": "45ms",
                "business_critical": True
            },
            "severity": "high",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "urgent"
        }

    # === CATEGORY 5: CONCURRENCY & PERFORMANCE (2 scenarios) ===
    
    @staticmethod
    def generate_memory_leak_error() -> Dict[str, Any]:
        """Memory exhaustion due to resource leak."""
        return {
            "ts": time.time(),
            "pid": 12356,
            "thread": "BackgroundWorker-5",
            "event": "exception",
            "func": "process_large_dataset",
            "file": "data_processor.py",
            "file_path": "/app/src/data_processor.py",
            "line": 234,
            "exception": {
                "type": "MemoryError",
                "message": "Unable to allocate 512 MiB for an array with shape (134217728,) and data type float64",
                "structured_traceback": [
                    {
                        "file": "/app/src/data_processor.py",
                        "line": 234,
                        "func": "process_large_dataset",
                        "code": "result = np.zeros((dataset_size,), dtype=np.float64)"
                    }
                ]
            },
            "locals": {
                "dataset_size": 134217728,
                "memory_usage": "12.8GB",
                "available_memory": "2.1GB",
                "process_id": 12356
            },
            "context": {
                "job_type": "data_analytics",
                "dataset_name": "customer_behavior_2024.csv",
                "file_size": "15GB",
                "processing_stage": "feature_extraction"
            },
            "severity": "critical",
            "business_impact": "medium",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }
    
    @staticmethod
    def generate_race_condition_error() -> Dict[str, Any]:
        """Race condition in shared resource access."""
        return {
            "ts": time.time(),
            "pid": 12357,
            "thread": "CacheWorker-12",
            "event": "exception",
            "func": "update_shared_cache",
            "file": "cache_manager.py",
            "file_path": "/app/src/cache_manager.py",
            "line": 145,
            "exception": {
                "type": "ConcurrentModificationError",
                "message": "Cache key 'user_sessions' modified by another thread during update",
                "structured_traceback": [
                    {
                        "file": "/app/src/cache_manager.py",
                        "line": 145,
                        "func": "update_shared_cache",
                        "code": "cache[key] = new_value  # Race condition here"
                    }
                ]
            },
            "locals": {
                "cache_key": "user_sessions",
                "new_value": {"sessions": 1247, "last_update": 1692210000},
                "thread_count": 24,
                "concurrent_writers": 8
            },
            "context": {
                "cache_type": "shared_memory",
                "high_concurrency": True,
                "cache_size": "256MB",
                "lock_contention": "high"
            },
            "severity": "high",
            "business_impact": "medium",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }

    # === ADDITIONAL CATEGORY 4: EXTERNAL API INTEGRATION (1 more scenario) ===
    
    @staticmethod
    def generate_third_party_service_outage() -> Dict[str, Any]:
        """Third-party service completely down."""
        return {
            "ts": time.time(),
            "pid": 12361,
            "thread": "EmailWorker-2",
            "event": "exception",
            "func": "send_notification_email",
            "file": "notification_service.py",
            "file_path": "/app/src/notification_service.py",
            "line": 92,
            "exception": {
                "type": "ConnectionError",
                "message": "HTTPSConnectionPool(host='api.sendgrid.com', port=443): Max retries exceeded",
                "structured_traceback": [
                    {
                        "file": "/app/src/notification_service.py",
                        "line": 92,
                        "func": "send_notification_email",
                        "code": "response = await sendgrid_client.send(message)"
                    }
                ]
            },
            "locals": {
                "recipient": "customer@example.com",
                "email_type": "order_confirmation",
                "retry_count": 5,
                "max_retries": 3
            },
            "context": {
                "email_provider": "sendgrid",
                "service_status": "major_outage",
                "fallback_provider": "mailgun",
                "business_critical": True
            },
            "severity": "high",
            "business_impact": "medium",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }

    # === ADDITIONAL CATEGORY 2: DATABASE & INFRASTRUCTURE (1 more scenario) ===
    
    @staticmethod
    def generate_disk_space_exhaustion() -> Dict[str, Any]:
        """Server disk space exhaustion."""
        return {
            "ts": time.time(),
            "pid": 12362,
            "thread": "LogWorker-1",
            "event": "exception",
            "func": "write_audit_log",
            "file": "logging_service.py",
            "file_path": "/app/src/logging_service.py",
            "line": 156,
            "exception": {
                "type": "OSError",
                "message": "[Errno 28] No space left on device",
                "structured_traceback": [
                    {
                        "file": "/app/src/logging_service.py",
                        "line": 156,
                        "func": "write_audit_log",
                        "code": "with open(log_file, 'a') as f: f.write(log_entry)"
                    }
                ]
            },
            "locals": {
                "log_file": "/var/log/app/audit.log",
                "log_entry": "User 12345 performed admin action...",
                "disk_usage": "99.8%",
                "available_space": "45MB"
            },
            "context": {
                "log_rotation_failed": True,
                "disk_partition": "/var",
                "log_level": "audit",
                "compliance_required": True
            },
            "severity": "critical",
            "business_impact": "high",
            "priority": "ALWAYS",
            "fix_urgency": "immediate"
        }

    # === ADDITIONAL CATEGORY 1: PAYMENT & E-COMMERCE (1 more scenario) ===
    
    @staticmethod  
    def generate_refund_processing_error() -> Dict[str, Any]:
        """Refund processing failure with financial impact."""
        return {
            "ts": time.time(),
            "pid": 12363,
            "thread": "RefundWorker-1",
            "event": "exception",
            "func": "process_refund",
            "file": "refund_service.py", 
            "file_path": "/app/src/refund_service.py",
            "line": 78,
            "exception": {
                "type": "RefundError",
                "message": "Cannot refund amount $450.00: exceeds original charge of $299.99",
                "structured_traceback": [
                    {
                        "file": "/app/src/refund_service.py",
                        "line": 78,
                        "func": "process_refund",
                        "code": "if refund_amount > original_charge: raise RefundError(...)"
                    }
                ]
            },
            "locals": {
                "refund_amount": 450.00,
                "original_charge": 299.99,
                "order_id": "ORD_2025_067",
                "refund_reason": "customer_complaint",
                "processing_fee": 15.00
            },
            "context": {
                "refund_type": "partial_refund",
                "customer_tier": "vip",
                "escalation_level": 2,
                "manual_override_available": True
            },
            "severity": "high",
            "business_impact": "medium",
            "priority": "ALWAYS",
            "fix_urgency": "normal"
        }

    # === CATEGORY 6: BUSINESS LOGIC & VALIDATION (3 scenarios) ===
    
    @staticmethod
    def generate_business_rule_violation() -> Dict[str, Any]:
        """Business rule validation failure."""
        return {
            "ts": time.time(),
            "pid": 12358,
            "thread": "OrderProcessor-6",
            "event": "exception",
            "func": "validate_bulk_discount",
            "file": "pricing_engine.py",
            "file_path": "/app/src/pricing_engine.py",
            "line": 189,
            "exception": {
                "type": "BusinessRuleViolationError",
                "message": "Bulk discount of 85% exceeds maximum allowed discount of 75%",
                "structured_traceback": [
                    {
                        "file": "/app/src/pricing_engine.py",
                        "line": 189,
                        "func": "validate_bulk_discount",
                        "code": "if discount_percentage > MAX_DISCOUNT_PERCENT: raise BusinessRuleViolationError(...)"
                    }
                ]
            },
            "locals": {
                "order_value": 15000.00,
                "item_count": 150,
                "calculated_discount": 0.85,
                "max_allowed_discount": 0.75,
                "customer_tier": "enterprise"
            },
            "context": {
                "order_type": "bulk_purchase",
                "customer_type": "b2b_enterprise",
                "approval_required": True,
                "manager_override": False
            },
            "severity": "medium",
            "business_impact": "medium",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }
    
    @staticmethod
    def generate_data_validation_error() -> Dict[str, Any]:
        """Input data validation failure."""
        return {
            "ts": time.time(),
            "pid": 12359,
            "thread": "APIWorker-11",
            "event": "exception",
            "func": "create_user_account",
            "file": "user_service.py",
            "file_path": "/app/src/user_service.py",
            "line": 67,
            "exception": {
                "type": "ValidationError",
                "message": "Invalid email format: 'user@invalid'",
                "structured_traceback": [
                    {
                        "file": "/app/src/user_service.py",
                        "line": 67,
                        "func": "create_user_account",
                        "code": "validate_email(user_data['email'])"
                    }
                ]
            },
            "locals": {
                "user_data": {
                    "name": "John Doe",
                    "email": "user@invalid",
                    "age": 25,
                    "country": "US"
                },
                "validation_errors": ["email_format"],
                "form_source": "mobile_app"
            },
            "context": {
                "registration_flow": "social_signup",
                "platform": "mobile_ios",
                "form_auto_fill": True,
                "validation_stage": "server_side"
            },
            "severity": "medium",
            "business_impact": "low",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }
    
    @staticmethod
    def generate_workflow_state_error() -> Dict[str, Any]:
        """Invalid workflow state transition."""
        return {
            "ts": time.time(),
            "pid": 12360,
            "thread": "WorkflowEngine-3",
            "event": "exception",
            "func": "transition_order_state",
            "file": "order_workflow.py",
            "file_path": "/app/src/order_workflow.py",
            "line": 112,
            "exception": {
                "type": "InvalidStateTransitionError",
                "message": "Cannot transition from 'cancelled' to 'shipped'",
                "structured_traceback": [
                    {
                        "file": "/app/src/order_workflow.py",
                        "line": 112,
                        "func": "transition_order_state",
                        "code": "self.state_machine.transition(current_state, target_state)"
                    }
                ]
            },
            "locals": {
                "order_id": "ORD_2025_089",
                "current_state": "cancelled",
                "target_state": "shipped",
                "user_id": 44556,
                "timestamp": 1692210000
            },
            "context": {
                "order_value": 89.99,
                "cancellation_reason": "customer_request",
                "fulfillment_center": "west_coast",
                "automated_transition": False
            },
            "severity": "medium",
            "business_impact": "low",
            "priority": "SAMPLE",
            "fix_urgency": "normal"
        }

    @classmethod
    def get_all_test_cases(cls) -> List[Dict[str, Any]]:
        """Get all 14 production failure scenarios across 6 categories."""
        return [
            # Category 1: Payment & E-commerce (4 scenarios)
            cls.generate_payment_processing_error(),
            cls.generate_payment_timeout_error(), 
            cls.generate_inventory_concurrency_error(),
            cls.generate_refund_processing_error(),
            
            # Category 2: Database & Infrastructure (4 scenarios)
            cls.generate_database_keyerror(),
            cls.generate_connection_pool_exhaustion(),
            cls.generate_deadlock_detection_error(),
            cls.generate_disk_space_exhaustion(),
            
            # Category 3: Authentication & Security (2 scenarios)
            cls.generate_auth_attributeerror(),
            cls.generate_jwt_expiration_error(),
            
            # Category 4: External API Integrations (4 scenarios)
            cls.generate_api_indexerror(),
            cls.generate_rate_limit_exceeded_error(),
            cls.generate_webhook_processing_error(),
            cls.generate_third_party_service_outage(),
            
            # Category 5: Concurrency & Performance (2 scenarios) 
            cls.generate_memory_leak_error(),
            cls.generate_race_condition_error(),
            
            # Category 6: Business Logic & Validation (3 scenarios)
            cls.generate_business_rule_violation(),
            cls.generate_data_validation_error(),
            cls.generate_workflow_state_error()
        ]
    
    @classmethod
    def get_test_scenarios_by_category(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Get test scenarios organized by category."""
        return {
            "payment_ecommerce": [
                cls.generate_payment_processing_error(),
                cls.generate_payment_timeout_error(),
                cls.generate_inventory_concurrency_error()
            ],
            "database_infrastructure": [
                cls.generate_database_keyerror(),
                cls.generate_connection_pool_exhaustion(),
                cls.generate_deadlock_detection_error()
            ],
            "authentication_security": [
                cls.generate_auth_attributeerror(),
                cls.generate_jwt_expiration_error()
            ],
            "external_api_integrations": [
                cls.generate_api_indexerror(),
                cls.generate_rate_limit_exceeded_error(),
                cls.generate_webhook_processing_error()
            ],
            "concurrency_performance": [
                cls.generate_memory_leak_error(),
                cls.generate_race_condition_error()
            ],
            "business_logic_validation": [
                cls.generate_business_rule_violation(),
                cls.generate_data_validation_error(),
                cls.generate_workflow_state_error()
            ]
        }