"""
Test suite for Multi-Agent HR Assistant.

This package contains comprehensive tests for all components of the multi-agent HR assistant project.

Test Structure:
- conftest.py: Shared fixtures and configuration
- test_entities.py: Domain entity tests
- test_intents.py: Intent type tests
- test_adapters.py: Infrastructure adapter tests
- test_agents.py: Agent implementation tests
- test_api_endpoints.py: FastAPI endpoint tests
- test_integration.py: Integration and workflow tests
- test_utilities.py: Utility function tests

Run tests with:
    pytest tests/
    pytest tests/ --cov=src/multi-agent-hr-assistant

For more information, see README.md and TEST_SUMMARY.md in this directory.
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent HR Assistant Team"
