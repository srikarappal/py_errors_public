# Demo Apps - Real Buggy Code for ThinkingSDK Autofix Testing

## Purpose

This directory contains **real, intentionally buggy applications** that demonstrate common Python errors and allow ThinkingSDK's autofix capabilities to be tested in realistic scenarios.

**IMPORTANT**: These are NOT tests for ThinkingSDK features. These are sample applications with real bugs that ThinkingSDK should detect and fix.

## Directory Structure

### `basic_errors/`
Simple, common Python errors that every developer encounters:
- JSON parsing errors
- NoneType attribute errors
- Array index out of bounds
- Unbound local variable errors
- Regex processing errors

**Purpose**: Test ThinkingSDK's ability to fix fundamental Python mistakes.

### `business_logic/`
Real-world business logic bugs that cause financial/operational problems:
- E-commerce inventory overselling
- Payment validation failures
- Order processing race conditions

**Purpose**: Test ThinkingSDK's understanding of business context and domain-specific fixes.

### `concurrency/`
Threading and async errors:
- Race conditions
- Deadlocks
- Thread-unsafe operations

**Purpose**: Test ThinkingSDK's ability to fix concurrency issues.

### `database_issues/`
Database-related errors:
- Connection failures
- Query errors
- Transaction handling bugs

**Purpose**: Test ThinkingSDK's database debugging capabilities.

### `api_networking/`
Network and API integration errors:
- HTTP request failures
- API endpoint errors
- Timeout handling
- JSON serialization issues

**Purpose**: Test ThinkingSDK's network error fixing.

### `memory_management/`
Memory-related bugs:
- Memory leaks
- Large object allocation issues
- Resource cleanup failures

**Purpose**: Test ThinkingSDK's memory profiling and optimization.

### `multiprocessing/`
Multi-process coordination errors:
- Process communication failures
- Shared state corruption
- Process pool errors

**Purpose**: Test ThinkingSDK's multiprocessing debugging.

### `security/`
Security vulnerabilities:
- SQL injection patterns
- XSS vulnerabilities
- Path traversal bugs

**Purpose**: Test ThinkingSDK's security fix capabilities.

### `long_running_servers/`
Server application errors:
- Resource exhaustion
- Connection pool issues
- Request handling bugs

**Purpose**: Test ThinkingSDK's server debugging.

## How To Use

### Running Individual Demo Apps

```bash
# Run a specific buggy app to trigger exceptions
cd demo_apps/basic_errors/
python json_file_processing_scenario.py

# ThinkingSDK client will capture the exception
# ThinkingSDK server will attempt to generate and test a fix
# Check the dashboard to see the fix attempt
```

### Running All Demo Apps

```bash
# From the root of py_errors_public/
python run_all_demos.py
```

### Expected Behavior

1. **Exception Triggered**: Demo app runs and hits a bug
2. **Captured by ThinkingSDK**: Client sends exception to server
3. **Autofix Attempted**: Server analyzes and generates fix
4. **PR Created**: Fix is committed to a branch and PR is opened
5. **Human Review**: Developer reviews the AI-generated fix

## Difference from `tests/`

| Directory | Purpose | Exception Handling | Autofix Behavior |
|-----------|---------|-------------------|------------------|
| `demo_apps/` | Real buggy code | Bugs are problems to fix | **SHOULD BE FIXED** |
| `tests/` | Test ThinkingSDK features | Exceptions are expected | **SHOULD NOT BE FIXED** |

### Example:

**In `demo_apps/basic_errors/json_file_processing_scenario.py`**:
```python
# BUG: Missing error handling
data = json.load(f)  # ← Will fail on malformed JSON
```
→ ThinkingSDK **SHOULD** fix this by adding try-except

**In `tests/scenarios/test_exception_grouping.py`**:
```python
# INTENTIONAL: Testing exception grouping
raise ValueError("Payment amount cannot be negative")  # ← Expected!
```
→ ThinkingSDK **SHOULD NOT** "fix" this - it's testing the grouping feature

## Adding New Demo Apps

To add a new buggy application:

1. Choose appropriate category directory (or create new one)
2. Write code with a **real, realistic bug**
3. Add ThinkingSDK client initialization:
   ```python
   import thinking_sdk_client as thinking
   thinking.start(api_key="...", server_url="http://localhost:8000")

   # Your buggy code here

   thinking.stop()
   ```
4. Document what bug it demonstrates
5. Run it to trigger the exception
6. Verify ThinkingSDK attempts a fix

## Guidelines for Demo Apps

### DO:
✅ Create realistic bugs that developers actually encounter
✅ Use real-world business logic and scenarios
✅ Make bugs fixable with reasonable AI-generated code
✅ Document what the bug is and why it's problematic

### DON'T:
❌ Create intentional exceptions for testing ThinkingSDK features (use `tests/` for that)
❌ Create unfixable bugs (e.g., requiring external system changes)
❌ Create security exploits or malicious code
❌ Create bugs that require human business decisions

## Contributing

When adding new demo apps, ensure they:
1. Represent real-world scenarios
2. Have clear bug descriptions
3. Can be fixed by AI without human business logic decisions
4. Include ThinkingSDK client integration
5. Run independently without complex setup

---

**Remember**: These are demo applications with real bugs. The `tests/` directory is for testing ThinkingSDK's features (exception grouping, deduplication, etc.).
