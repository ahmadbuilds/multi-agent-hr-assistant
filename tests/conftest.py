"""
Pytest configuration and shared fixtures for the test suite.
"""
import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "multi-agent-hr-assistant"))

from domain.entities import UserQuery, TicketCreation, Supervisor_structured_output
from domain.intents import IntentType, TicketType, AgentName
from application.states import ClerkState, LibrarianState, SupervisorState
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from collections import deque


@pytest.fixture
def sample_user_query():
    """Fixture for a sample UserQuery."""
    return UserQuery(
        query="I need to request leave for 5 days",
        conversation_id="conv_123",
        user_id="user_456",
        auth_token="token_xyz",
        UploadedText="",
        isAdmin=False,
        attachment_url=None,
        attachment_name=None
    )


@pytest.fixture
def sample_ticket_creation():
    """Fixture for a sample TicketCreation."""
    return TicketCreation(
        ticket_type="leave",
        subject="Leave Request",
        description="Requesting 5 days of leave",
        status="in_progress",
        leave_days=5,
        accepted=None
    )


@pytest.fixture
def sample_clerk_state():
    """Fixture for a sample ClerkState."""
    user_query = UserQuery(
        query="Get my leave balance",
        conversation_id="conv_123",
        user_id="user_456",
        auth_token="token_xyz",
    )
    return ClerkState(
        user_query=user_query,
        messages=[],
        pending_tasks=deque(),
        tool_results=[],
        final_response=deque(),
        hitl_state=deque(),
        next_step=None
    )


@pytest.fixture
def sample_librarian_state():
    """Fixture for a sample LibrarianState."""
    user_query = UserQuery(
        query="Retrieve policy documents",
        conversation_id="conv_123",
        user_id="user_456",
        auth_token="token_xyz",
    )
    return LibrarianState(
        user_query=user_query,
        messages=[],
        action=[],
        hitl_state=[],
        next_step=None,
        response=None
    )


@pytest.fixture
def sample_supervisor_state():
    """Fixture for a sample SupervisorState."""
    user_query = UserQuery(
        query="I need help with my leave request",
        conversation_id="conv_123",
        user_id="user_456",
        auth_token="token_xyz",
    )
    return SupervisorState(
        user_query=user_query,
        messages=[],
        active_agent="Supervisor",
        identified_intent=[],
        final_response=None,
        next_steps=None
    )


@pytest.fixture
def mock_llm_model():
    """Fixture for a mock LLM model."""
    mock_llm = Mock()
    mock_llm.invoke = Mock()
    mock_llm.ainvoke = AsyncMock()
    return mock_llm


@pytest.fixture
def mock_async_llm_model():
    """Fixture for a mock async LLM model."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke = AsyncMock()
    return mock_llm


@pytest.fixture
def mock_leave_balance_port():
    """Fixture for a mock LeaveBalancePort."""
    mock_port = Mock()
    mock_port.get_leave_balance = Mock(return_value=15)
    return mock_port


@pytest.fixture
def mock_ticket_creation_port():
    """Fixture for a mock TicketCreationPort."""
    mock_port = Mock()
    mock_port.create_ticket = Mock(return_value=True)
    return mock_port


@pytest.fixture
def mock_supabase_client():
    """Fixture for a mock Supabase client."""
    mock_client = Mock()
    mock_client.auth.get_user = Mock()
    mock_client.table = Mock()
    return mock_client


@pytest.fixture
def mock_redis_client():
    """Fixture for a mock Redis client."""
    mock_client = AsyncMock()
    mock_client.set = AsyncMock(return_value=True)
    mock_client.get = AsyncMock(return_value=None)
    mock_client.delete = AsyncMock(return_value=True)
    return mock_client


@pytest.fixture
def mock_socket_manager():
    """Fixture for a mock Socket Manager."""
    mock_manager = Mock()
    mock_manager.emit = Mock()
    mock_manager.emit_admin_notification = Mock()
    return mock_manager


@pytest.fixture
def environment_variables(monkeypatch):
    """Fixture to set environment variables for testing."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test_service_key")
    monkeypatch.setenv("MOCK_API_KEY_CLERK", "https://api.test.com")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")


@pytest.fixture
def ai_message():
    """Fixture for a sample AI message."""
    return AIMessage(content="This is a test message from the AI")


@pytest.fixture
def human_message():
    """Fixture for a sample Human message."""
    return HumanMessage(content="This is a test query from the user")
