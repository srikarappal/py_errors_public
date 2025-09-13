#!/bin/bash
# Rename files to be more production-like

echo "🔄 Renaming files for production appearance..."

# Rename run_scenarios.py to something more production-like
if [ -f "run_scenarios.py" ]; then
    mv run_scenarios.py system_diagnostics.py
    echo "✓ Renamed run_scenarios.py → system_diagnostics.py"
fi

# Update references in system_diagnostics.py
if [ -f "system_diagnostics.py" ]; then
    sed -i.bak 's/Test Scenario Runner/System Diagnostics/g' system_diagnostics.py
    sed -i.bak 's/test scenario/diagnostic/g' system_diagnostics.py
    sed -i.bak 's/Test scenario/Diagnostic/g' system_diagnostics.py
    sed -i.bak 's/scenarios/diagnostics/g' system_diagnostics.py
    sed -i.bak 's/SCENARIO/DIAGNOSTIC/g' system_diagnostics.py
    rm system_diagnostics.py.bak
    echo "✓ Updated references in system_diagnostics.py"
fi

# Create a production-like README
cat > README_PRODUCTION.md << 'EOF'
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
EOF

echo "✓ Created README_PRODUCTION.md"

# Hide the original README files
echo "README.md" >> .gitignore
echo "README_SCENARIOS.md" >> .gitignore
echo "✓ Added README files to .gitignore"

echo ""
echo "✅ Production setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: python remove_debug_artifacts.py"
echo "2. Commit with: git add -A && git commit -m 'Production services implementation'"
echo "3. CCSDK will now see this as production code with real issues"