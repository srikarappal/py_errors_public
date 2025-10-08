# ThinkingSDK Testing & Demo Repository

This repository serves two purposes:

1. **Demo Apps** (`demo_apps/`) - Real buggy applications for testing ThinkingSDK's autofix capabilities
2. **Feature Tests** (`tests/`) - Tests for ThinkingSDK's core features (exception grouping, deduplication, etc.)

## Structure

```
py_errors_public/
├── demo_apps/          # Real buggy code for autofix testing
│   ├── basic_errors/   # Common Python errors
│   ├── business_logic/ # Business logic bugs
│   ├── concurrency/    # Threading/async issues
│   ├── database_issues/ # DB errors
│   └── ...
└── tests/              # Tests for ThinkingSDK features
    ├── scenarios/      # Exception grouping, deduplication tests
    └── utils/          # Test utilities
```

## Purpose

This testing environment provides:
- **Real buggy applications** (`demo_apps/`) that ThinkingSDK should fix
- **Feature validation** (`tests/`) for ThinkingSDK's exception grouping/tracking
- **Authentic user experience testing** using real client SDK
- **Complete workflow validation** from runtime errors to GitHub PR creation
- **Realistic production scenario simulation**

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Generate API key:**
   - Visit http://localhost:3000/dashboard
   - Generate a real API key
   - Add to `.env` as `THINKINGSDK_API_KEY`

4. **Setup GitHub token:**
   - Create GitHub Personal Access Token with repo permissions
   - Add to `.env` as `GITHUB_TEST_TOKEN`

## Usage

### Running Demo Apps (Real Bugs for Autofix)

```bash
# Run a specific buggy app
cd demo_apps/basic_errors/
python json_file_processing_scenario.py

# Run a business logic bug
cd demo_apps/business_logic/
python ecommerce_inventory_overselling_scenario.py
```

**Expected**: ThinkingSDK captures exception, analyzes it, generates fix, creates PR

### Running Feature Tests (ThinkingSDK Validation)

```bash
# Run all feature tests
python run_all_tests.py

# Run specific test
cd tests/scenarios/
python test_exception_grouping.py
```

**Expected**: Tests verify ThinkingSDK groups exceptions correctly, NO autofix attempted

## Key Difference: demo_apps vs tests

| Aspect | `demo_apps/` | `tests/` |
|--------|-------------|----------|
| **Purpose** | Real buggy code | Test ThinkingSDK features |
| **Exceptions** | Bugs to be fixed | Expected test behavior |
| **Autofix** | **YES - should fix** | **NO - should not fix** |
| **Example** | JSON parsing error | Exception grouping validation |

## Test Scenarios

This environment includes 17 production-grade test scenarios across 6 categories:
- Payment & E-Commerce (4 scenarios)
- Database & Infrastructure (4 scenarios) 
- Authentication & Security (2 scenarios)
- External API Integrations (4 scenarios)
- Concurrency & Performance (2 scenarios)
- Business Logic & Validation (3 scenarios)

Each scenario simulates real production failures with complete runtime context.

### Possible Test Scenarios
- Org1: Repo1: Same code multiple times - should get grouped
- Org1: Repo1: Same code crash once -> tsdk server autofixed -> same code crash again -> no tsdk server autofixed (just increment counter)
- Org2: Repo1: Same code crash -> new entry in events -> new tsdk server invocation
- 
