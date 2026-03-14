# Quick Test Reference Guide

## InstallTest Dependencies

```bash
pip install -r tests/requirements-test.txt
```

## Basic Commands

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Category

```bash
pytest tests/test_entities.py          # Domain entities
pytest tests/test_intents.py           # Intent types
pytest tests/test_adapters.py          # Adapters
pytest tests/test_agents.py            # Agents
pytest tests/test_api_endpoints.py     # API routes
pytest tests/test_integration.py       # Workflows
pytest tests/test_utilities.py         # Utilities
```

### Run With Coverage

```bash
pytest tests/ --cov=src/multi-agent-hr-assistant --cov-report=html
```

### Run Specific Test

```bash
pytest tests/test_entities.py::TestUserQuery::test_user_query_creation
```

## Using the Test Runner Script

```bash
# Make script executable
chmod +x tests/run_tests.py

# Run different test suites
python tests/run_tests.py all           # All tests
python tests/run_tests.py unit          # Unit tests only
python tests/run_tests.py integration   # Integration tests
python tests/run_tests.py agents        # Agent tests
python tests/run_tests.py coverage      # With coverage report
python tests/run_tests.py html          # Generate HTML report
python tests/run_tests.py parallel      # Run in parallel
python tests/run_tests.py watch         # Watch mode
```

## Environment Setup

### Set Environment Variables

```bash
export SUPABASE_URL=https://test.supabase.co
export SUPABASE_KEY=test_key
export MOCK_API_KEY_CLERK=https://api.test.com
export GROQ_API_KEY=test_groq_key
```

### Windows (PowerShell)

```powershell
$env:SUPABASE_URL = "https://test.supabase.co"
$env:SUPABASE_KEY = "test_key"
$env:MOCK_API_KEY_CLERK = "https://api.test.com"
$env:GROQ_API_KEY = "test_groq_key"
```

## Advanced Options

### Verbose Output

```bash
pytest tests/ -vv --tb=long
```

### Run Only Failed Tests

```bash
pytest tests/ --lf
```

### Run Until First Failure

```bash
pytest tests/ -x
```

### Parallel Execution (requires pytest-xdist)

```bash
pytest tests/ -n auto
```

### Show Print Statements

```bash
pytest tests/ -s
```

### Set Timeout (requires pytest-timeout)

```bash
pytest tests/ --timeout=30
```

## Output Reports

### HTML Report

```bash
pytest tests/ --html=report.html --self-contained-html
```

### Coverage HTML Report

```bash
pytest tests/ --cov=src/multi-agent-hr-assistant --cov-report=html
# Open htmlcov/index.html in browser
```

### JUnit XML (for CI/CD)

```bash
pytest tests/ --junit-xml=junit.xml
```

## Troubleshooting

### ModuleNotFoundError

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

### Async Test Issues

```bash
# Ensure pytest-asyncio is properly installed
pip install --upgrade pytest-asyncio
```

### Port Already in Use

```bash
# Many tests use mocking to avoid port conflicts
# If you see port errors, check if other services are running
lsof -i :6379  # Check Redis port
```

## Test Development Workflow

### 1. Create Test File

```python
# tests/test_new_feature.py
import pytest

class TestNewFeature:
    def test_something(self):
        assert True
```

### 2. Run Test

```bash
pytest tests/test_new_feature.py -v
```

### 3. Watch Changes

```bash
pytest-watch tests/test_new_feature.py -- -v
```

### 4. Check Coverage

```bash
pytest tests/test_new_feature.py --cov=src/multi-agent-hr-assistant
```

## Continuous Integration

### Pre-commit Hook

```bash
# Install pre-commit
pip install pre-commit

# Run tests before commit
pre-commit run pytest --all-files
```

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r tests/requirements-test.txt
      - run: pytest tests/ --cov
```

## Performance Optimization

### Run Fastest Tests First

```bash
pytest tests/ -k "not slow"
```

### Profile Test Execution

```bash
pytest tests/ --durations=10
```

### Parallel Execution (faster)

```bash
pytest tests/ -n auto --dist loadscope
```

## Test Markers

### Run Tests by Marker

```bash
pytest tests/ -m "unit"
pytest tests/ -m "integration"
pytest tests/ -m "async"
pytest tests/ -m "not slow"
```

### Available Markers

- `unit`: Unit tests
- `integration`: Integration tests
- `async`: Asynchronous tests
- `slow`: Long-running tests
- `mock`: Tests using mocks
- `api`: API endpoint tests
- `entity`: Entity/model tests
- `smoke`: Quick smoke tests

## Common Issues & Solutions

| Issue            | Solution                                 |
| ---------------- | ---------------------------------------- |
| Import errors    | Set PYTHONPATH to include src/           |
| Async tests fail | Install pytest-asyncio                   |
| Tests are slow   | Run with -n auto for parallel            |
| Port conflicts   | Tests use mocks, check existing services |
| Coverage gaps    | Run with --cov-report=term-missing       |
| Flaky tests      | Check for timing issues, use --tb=short  |

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Test README.md](README.md)
- [Test Summary](TEST_SUMMARY.md)
- [Fixtures Guide](conftest.py)
