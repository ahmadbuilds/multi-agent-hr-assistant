# Test Suite Documentation

## Overview

This directory contains comprehensive test cases for the Multi-Agent HR Assistant project. The test suite covers unit tests, integration tests, and end-to-end tests across all major components.

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures and configuration
├── test_entities.py            # Domain Entity tests
├── test_intents.py             # Intent Type tests
├── test_adapters.py            # Infrastructure Adapter tests
├── test_agents.py              # Agent Implementation tests
├── test_api_endpoints.py       # FastAPI Endpoint tests
├── test_integration.py         # Integration & Workflow tests
├── test_utilities.py           # Utility Function tests
└── README.md                   # This file
```

## Test Coverage

### 1. **test_entities.py** - Domain Models

- **UserQuery**: User input validation and creation
- **TicketCreation**: Ticket entity validation
- **Classifications**: Various classification output models
- **AgentState**: Agent state management
- **TaskIntent**: Task decomposition and intent handling

**Key Test Cases:**

- 20+ entity validation tests
- Required field enforcement
- Type validation
- Serialization/Deserialization

### 2. **test_intents.py** - Intent Management

- Intent type validation
- Supervisor-only intent handling
- Agent name validation
- Action type validation

**Key Test Cases:**

- 30+ intent routing and validation tests
- Intent classification logic
- Agent-to-intent mapping

### 3. **test_adapters.py** - Infrastructure Adapters

- **ClerkLeaveBalanceAdapter**: External API interactions
- Port interface implementations
- Error handling and resilience

**Key Test Cases:**

- 10+ adapter tests
- API call mocking
- Error recovery scenarios
- Response parsing

### 4. **test_agents.py** - Agent Implementations

- **ClerkAgent**: Leave and ticket handling
- **LibrarianAgent**: Policy management
- **SupervisorAgent**: Query decomposition and routing

**Key Test Cases:**

- 20+ agent behavior tests
- LLM response parsing
- State transitions
- Error handling
- Decision node logic

### 5. **test_api_endpoints.py** - FastAPI Endpoints

- Query processing endpoint
- Authentication validation
- Authorization checking
- Input/Output validation

**Key Test Cases:**

- 15+ endpoint tests
- Response formatting
- Error handling
- Content type negotiation

### 6. **test_integration.py** - End-to-End Workflows

- Complete workflow execution
- Multi-agent coordination
- State management across agents
- Message flow and conversation context
- Error recovery and resilience
- Performance characteristics

**Key Test Cases:**

- 25+ integration tests
- Workflow orchestration
- Cross-component interaction
- Data persistence
- Scalability validation

### 7. **test_utilities.py** - Utility Functions

- Intent routing logic
- Task validation
- Conversation context management
- Ticket workflow validation
- Leave balance operations

**Key Test Cases:**

- 20+ utility function tests
- Business logic validation
- Workflow logic testing

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install pytest-testdox  # For detailed test reporting

# Install project dependencies
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_entities.py -v
pytest tests/test_agents.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_entities.py::TestUserQuery -v
```

### Run Specific Test Function

```bash
pytest tests/test_entities.py::TestUserQuery::test_user_query_creation -v
```

### Run with Coverage Report

```bash
pytest tests/ --cov=src/multi-agent-hr-assistant --cov-report=html
```

### Run Only Unit Tests

```bash
pytest tests/test_entities.py tests/test_intents.py tests/test_utilities.py -v
```

### Run Only Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Run Async Tests Only

```bash
pytest tests/test_agents.py tests/test_integration.py -v -k "async"
```

### Run with Markers

```bash
# Create markers in tests and run:
pytest -m "integration" -v
```

### Watch Mode (Auto-rerun on changes)

```bash
pytest-watch tests/ -- -v
```

### Generate HTML Report

```bash
pytest tests/ --html=report.html --self-contained-html
```

## Test Configuration

### pytest.ini Settings

- Test discovery pattern: `test_*.py`
- Minimum Python version: 3.8
- Async test framework: asyncio
- Coverage minimum: 80%

### Environment Variables for Testing

```
SUPABASE_URL=https://test.supabase.co
SUPABASE_KEY=test_key
SUPABASE_SERVICE_KEY=test_service_key
MOCK_API_KEY_CLERK=https://api.test.com
GROQ_API_KEY=test_groq_key
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Fixtures

### Available Fixtures (from conftest.py)

**Data Fixtures:**

- `sample_user_query`: Sample UserQuery object
- `sample_ticket_creation`: Sample TicketCreation object
- `sample_clerk_state`: Sample ClerkState
- `sample_librarian_state`: Sample LibrarianState
- `sample_supervisor_state`: Sample SupervisorState
- `ai_message`: Sample AIMessage
- `human_message`: Sample HumanMessage

**Mock Fixtures:**

- `mock_llm_model`: Mock LLM for sync operations
- `mock_async_llm_model`: Mock LLM for async operations
- `mock_leave_balance_port`: Mock LeaveBalancePort
- `mock_ticket_creation_port`: Mock TicketCreationPort
- `mock_supabase_client`: Mock Supabase client
- `mock_redis_client`: Mock Redis client
- `mock_socket_manager`: Mock Socket Manager

**Configuration Fixtures:**

- `environment_variables`: Set test environment variables

## Writing New Tests

### Test Template

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Test cases for new feature."""

    def test_feature_basic(self, required_fixture):
        """Test basic functionality."""
        # Arrange
        expected = "value"

        # Act
        result = required_fixture.method()

        # Assert
        assert result == expected

    @pytest.mark.asyncio
    async def test_feature_async(self, mock_async_llm_model):
        """Test async functionality."""
        # Arrange, Act, Assert
        pass
```

### Best Practices

1. **Use descriptive names**: `test_user_query_with_attachment_success()`
2. **Use docstrings**: Explain what is being tested
3. **Use fixtures**: Leverage conftest.py for common objects
4. **Mock external dependencies**: Don't call real APIs in tests
5. **Arrange-Act-Assert**: Structure tests clearly
6. **Test both success and failure**: Include error cases
7. **Use parametrize for variations**: Test multiple scenarios efficiently

## Continuous Integration

### GitHub Actions Example

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
      - run: pip install -r requirements-test.txt
      - run: pytest tests/ --cov=src/multi-agent-hr-assistant
```

## Troubleshooting

### Common Issues

**Issue: ImportError when running tests**

```bash
# Solution: Ensure environment is set up correctly
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/
```

**Issue: Async tests not running**

```bash
# Solution: Ensure pytest-asyncio is installed
pip install pytest-asyncio
# And add marker or use conftest.py
```

**Issue: Mocks not working as expected**

```bash
# Solution: Check patch paths are correct
from unittest.mock import patch
patch('module.path.ClassName')  # Use full path
```

**Issue: Tests passing locally but failing in CI**

```bash
# Solution: Check environment variables and dependencies
# Use same Python version as CI
# Check for timezone/locale specific code
```

## Performance Benchmarks

Expected test execution times:

- **Unit Tests**: ~1-2 seconds
- **Integration Tests**: ~3-5 seconds
- **Full Suite**: ~10-15 seconds

## Code Quality Metrics

Target metrics:

- **Code Coverage**: >80%
- **Test Pass Rate**: 100%
- **No Warnings**: Clean pytest output

## Contributing New Tests

1. Create test file following naming convention: `test_*.py`
2. Include docstrings for all test functions
3. Use existing fixtures when possible
4. Add new fixtures to `conftest.py` if needed
5. Run `pytest` locally before submitting
6. Document test scenarios in comments

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html)
- [Unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

## Contact & Support

For questions or issues with the test suite:

1. Check this README
2. Review existing test implementations
3. Run tests with `-vv` flag for verbose output
4. Use pytest's `--tb=long` for detailed tracebacks
