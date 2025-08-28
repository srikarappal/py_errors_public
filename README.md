# ThinkingSDK E2E Testing

Independent end-to-end testing environment that uses the real `thinking_sdk_client` to test against `thinking_sdk_server`.

## Purpose

This testing environment provides:
- **Authentic user experience testing** using real client SDK
- **Complete workflow validation** from runtime errors to GitHub PR creation
- **Isolated testing environment** separate from dashboard/server codebases
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
   - Add to `.env` as `THINKING_SDK_API_KEY`

4. **Setup GitHub token:**
   - Create GitHub Personal Access Token with repo permissions
   - Add to `.env` as `GITHUB_TEST_TOKEN`

## Usage

```bash
# Run all test scenarios
python run_all_tests.py

# Run specific scenario
python test_scenario.py --scenario payment_processing_error

# Run with GitHub integration
python test_github_flow.py
```

## Test Scenarios

This environment includes 17 production-grade test scenarios across 6 categories:
- Payment & E-Commerce (4 scenarios)
- Database & Infrastructure (4 scenarios) 
- Authentication & Security (2 scenarios)
- External API Integrations (4 scenarios)
- Concurrency & Performance (2 scenarios)
- Business Logic & Validation (3 scenarios)

Each scenario simulates real production failures with complete runtime context.
