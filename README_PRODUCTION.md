# Production Services

This repository contains production microservices and utilities.

## Services

- `basic_errors/` - Core error handling utilities
- `database_issues/` - Database connection management
- `api_networking/` - API client implementations
- `memory_management/` - Memory optimization utilities
- `concurrency/` - Thread pool and concurrent processing
- `multiprocessing/` - Multi-process task distribution
- `long_running_servers/` - Server implementations
- `business_logic/` - E-commerce business logic
- `security/` - Security and authentication services

## Running Diagnostics

To check system health:
```bash
python system_diagnostics.py --list  # List available checks
python system_diagnostics.py all     # Run all diagnostics
```

## Configuration

Ensure `thinkingsdk.yaml` is properly configured with your environment settings.
