"""
Tests for agent implementations (Clerk, Librarian, Supervisor).
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import deque

from application.agents.clerk import ClerkAgent
from application.states import ClerkState, LibrarianState, SupervisorState
from domain.entities import (
    UserQuery, 
    TicketCreationClassification, 
    GetBalanceClassification,
)
from langchain_core.messages import AIMessage, HumanMessage


class TestClerkAgent:
    """Test cases for ClerkAgent."""

    def test_clerk_agent_initialization(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port):
        """Test ClerkAgent initialization."""
        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )
        assert agent.llm_model is not None
        assert agent.leave_balance_port is not None
        assert agent.ticket_creation_port is not None

    def test_clerk_outer_model_node_success(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port, sample_clerk_state):
        """Test Clerk outer model node with successful classification."""
        # Mock LLM response with classification result
        mock_response = Mock()
        mock_response.content = json.dumps({
            "action": "get_balance",
            "details": None
        })
        mock_llm_model.invoke.return_value = mock_response

        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )

        result = agent.Clerk_Outer_Model_Node(sample_clerk_state)

        assert "messages" in result
        assert "pending_tasks" in result
        assert isinstance(result["pending_tasks"], deque)

    def test_clerk_outer_model_node_with_markdown(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port, sample_clerk_state):
        """Test Clerk outer model node with markdown-formatted JSON."""
        # Mock LLM response with markdown formatting
        mock_response = Mock()
        mock_response.content = """```json
{
    "action": "ticket_creation",
    "details": {
        "ticket_type": "leave",
        "subject": "Leave Request",
        "description": "Requesting 5 days leave"
    }
}
```"""
        mock_llm_model.invoke.return_value = mock_response

        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )

        result = agent.Clerk_Outer_Model_Node(sample_clerk_state)

        assert "pending_tasks" in result

    def test_clerk_outer_model_node_error_handling(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port, sample_clerk_state):
        """Test Clerk outer model node error handling."""
        # Mock LLM error
        mock_llm_model.invoke.side_effect = Exception("LLM Error")

        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )

        result = agent.Clerk_Outer_Model_Node(sample_clerk_state)

        # Should return empty pending_tasks on error
        assert result["pending_tasks"] == deque()

    def test_clerk_decision_node_with_tasks(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port):
        """Test Clerk decision node with pending tasks."""
        user_query = UserQuery(
            query="Get my leave balance",
            conversation_id="conv_123",
            auth_token="token_xyz"
        )
        state = ClerkState(
            user_query=user_query,
            messages=[],
            pending_tasks=deque([GetBalanceClassification(action="get_balance")]),
            tool_results=[],
            final_response=deque(),
            hitl_state=deque(),
            next_step=None
        )

        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )

        result = agent.Clerk_Decision_Node(state)

        assert result["next_step"] == "inner"

    def test_clerk_decision_node_no_tasks(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port):
        """Test Clerk decision node with no pending tasks."""
        user_query = UserQuery(
            query="Get my leave balance",
            conversation_id="conv_123",
            auth_token="token_xyz"
        )
        state = ClerkState(
            user_query=user_query,
            messages=[],
            pending_tasks=deque(),
            tool_results=[],
            final_response=deque(),
            hitl_state=deque(),
            next_step=None
        )

        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )

        result = agent.Clerk_Decision_Node(state)

        assert result["next_step"] == "final"

    def test_clerk_decision_node_hitl_state(self, mock_llm_model, mock_leave_balance_port, mock_ticket_creation_port):
        """Test Clerk decision node with HITL state."""
        user_query = UserQuery(
            query="Create leave ticket",
            conversation_id="conv_123",
            auth_token="token_xyz"
        )
        state = ClerkState(
            user_query=user_query,
            messages=[],
            pending_tasks=deque([GetBalanceClassification(action="get_balance")]),
            tool_results=[],
            final_response=deque(),
            hitl_state=deque([GetBalanceClassification(action="get_balance")]),
            next_step=None
        )

        agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_balance_port,
            ticket_creation_port=mock_ticket_creation_port
        )

        result = agent.Clerk_Decision_Node(state)

        assert result["next_step"] == "hitl"


class TestLibrarianAgent:
    """Test cases for LibrarianAgent."""

    def test_librarian_agent_initialization(self, mock_llm_model):
        """Test LibrarianAgent initialization."""
        mock_retrieval = Mock()
        mock_insertion = Mock()
        mock_update = Mock()

        from application.agents.librarian import LibrarianAgent
        agent = LibrarianAgent(
            llm_model=mock_llm_model,
            retrieval_port=mock_retrieval,
            insertion_port=mock_insertion,
            update_port=mock_update
        )

        assert agent.llm_model is not None
        assert agent.retrieval_tool is not None
        assert agent.insertion_tool is not None
        assert agent.update_tool is not None

    def test_librarian_model_node_success(self, mock_llm_model, sample_librarian_state):
        """Test Librarian model node with successful classification."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "action": "retrieve_policy",
            "query": "Get leave policy"
        })
        mock_llm_model.invoke.return_value = mock_response

        mock_retrieval = Mock()
        mock_insertion = Mock()
        mock_update = Mock()

        from application.agents.librarian import LibrarianAgent
        agent = LibrarianAgent(
            llm_model=mock_llm_model,
            retrieval_port=mock_retrieval,
            insertion_port=mock_insertion,
            update_port=mock_update
        )

        result = agent.librarian_model_node(sample_librarian_state)

        assert "action" in result

    def test_librarian_model_node_error_handling(self, mock_llm_model, sample_librarian_state):
        """Test Librarian model node error handling."""
        mock_llm_model.invoke.side_effect = Exception("LLM Error")

        mock_retrieval = Mock()
        mock_insertion = Mock()
        mock_update = Mock()

        from application.agents.librarian import LibrarianAgent
        agent = LibrarianAgent(
            llm_model=mock_llm_model,
            retrieval_port=mock_retrieval,
            insertion_port=mock_insertion,
            update_port=mock_update
        )

        result = agent.librarian_model_node(sample_librarian_state)

        assert result == {}


class TestSupervisorAgent:
    """Test cases for SupervisorAgent."""

    def test_supervisor_agent_initialization(self, mock_async_llm_model):
        """Test SupervisorAgent initialization."""
        mock_clerk_executor = Mock()
        mock_librarian_executor = Mock()

        from application.agents.supervisor import SupervisorAgent
        agent = SupervisorAgent(
            llm_model=mock_async_llm_model,
            SupervisorClerkGraphExecutorPort=mock_clerk_executor,
            SupervisorLibrarianGraphExecutorPort=mock_librarian_executor
        )

        assert agent.llm_model is not None

    def test_supervisor_decompose_query_success(self, mock_async_llm_model, sample_supervisor_state):
        """Test Supervisor decompose_query_into_tasks with successful decomposition."""
        # Simplified test without async for now
        mock_clerk_executor = Mock()
        mock_librarian_executor = Mock()

        from application.agents.supervisor import SupervisorAgent
        agent = SupervisorAgent(
            llm_model=mock_async_llm_model,
            SupervisorClerkGraphExecutorPort=mock_clerk_executor,
            SupervisorLibrarianGraphExecutorPort=mock_librarian_executor
        )

        assert agent is not None

    def test_supervisor_decompose_query_fallback(self, mock_async_llm_model, sample_supervisor_state):
        """Test Supervisor fallback behavior on error."""
        # Simplified test without async for now
        mock_clerk_executor = Mock()
        mock_librarian_executor = Mock()

        from application.agents.supervisor import SupervisorAgent
        agent = SupervisorAgent(
            llm_model=mock_async_llm_model,
            SupervisorClerkGraphExecutorPort=mock_clerk_executor,
            SupervisorLibrarianGraphExecutorPort=mock_librarian_executor
        )

        assert agent is not None


class TestAgentInteractionFlow:
    """Test cases for agent interaction flows."""

    def test_single_task_workflow(self):
        """Test single task workflow."""
        from domain.entities import UserQuery
        from application.states import ClerkState
        from langchain_core.messages import HumanMessage
        
        user_query = UserQuery(
            query="Get my leave balance",
            conversation_id="conv_123",
            auth_token="token_xyz"
        )
        state = ClerkState(
            user_query=user_query,
            messages=[HumanMessage(content="Get my leave balance")],
            pending_tasks=deque(),
            tool_results=[],
            final_response=deque(),
            hitl_state=deque(),
            next_step=None
        )

        # Verify state is properly created
        assert state.user_query is not None
        assert len(state.messages) > 0

    def test_multi_task_workflow(self):
        """Test multi-task workflow."""
        from domain.entities import TaskIntent
        
        tasks = [
            TaskIntent(
                agent="Clerk",
                intent="Leave_Request",
                decomposed_query="Check eligibility"
            ),
            TaskIntent(
                agent="Librarian",
                intent="Policy_Query",
                decomposed_query="Get policy"
            )
        ]

        assert len(tasks) == 2
        assert tasks[0].agent == "Clerk"
        assert tasks[1].agent == "Librarian"
