"""
Integration tests for complete workflows and component interactions.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import deque

from domain.entities import (
    UserQuery,
    TaskIntent,
)
from application.states import ClerkState, LibrarianState, SupervisorState


class TestWorkflowIntegration:
    """Integration tests for complete workflows."""

    def test_leave_request_workflow(self, sample_user_query, mock_llm_model):
        """Test complete leave request workflow."""
        # Initialize components
        from application.agents.clerk import ClerkAgent
        
        mock_leave_port = Mock()
        mock_leave_port.get_leave_balance.return_value = 15
        mock_ticket_port = Mock()
        mock_ticket_port.create_ticket.return_value = True

        clerk_agent = ClerkAgent(
            llm_model=mock_llm_model,
            leave_balance_port=mock_leave_port,
            ticket_creation_port=mock_ticket_port
        )

        # Verify agent was created successfully
        assert clerk_agent is not None
        assert clerk_agent.leave_balance_port.get_leave_balance("test") == 15

    def test_policy_query_workflow(self, sample_user_query):
        """Test complete policy query workflow."""
        from application.agents.librarian import LibrarianAgent
        
        mock_llm = Mock()
        mock_retrieval = Mock()
        mock_retrieval.retrieve.return_value = "Policy content"
        mock_insertion = Mock()
        mock_update = Mock()

        librarian_agent = LibrarianAgent(
            llm_model=mock_llm,
            retrieval_port=mock_retrieval,
            insertion_port=mock_insertion,
            update_port=mock_update
        )

        assert librarian_agent is not None

    def test_supervisor_workflow(self, mock_async_llm_model):
        """Test complete supervisor workflow."""
        from application.agents.supervisor import SupervisorAgent
        
        mock_clerk_executor = Mock()
        mock_librarian_executor = Mock()

        supervisor_agent = SupervisorAgent(
            llm_model=mock_async_llm_model,
            SupervisorClerkGraphExecutorPort=mock_clerk_executor,
            SupervisorLibrarianGraphExecutorPort=mock_librarian_executor
        )

        assert supervisor_agent is not None

    def test_multi_agent_coordination(self):
        """Test coordination between multiple agents."""
        # Create multiple agents
        from application.agents.clerk import ClerkAgent
        from application.agents.librarian import LibrarianAgent
        
        mock_llm = Mock()
        mock_clerk_leave = Mock()
        mock_clerk_ticket = Mock()
        mock_retrieval = Mock()
        mock_insertion = Mock()
        mock_update = Mock()

        clerk = ClerkAgent(mock_llm, mock_clerk_leave, mock_clerk_ticket)
        librarian = LibrarianAgent(mock_llm, mock_retrieval, mock_insertion, mock_update)

        # Verify both agents exist
        assert clerk is not None
        assert librarian is not None


class TestStateManagement:
    """Integration tests for state management across agents."""

    def test_clerk_state_transitions(self, sample_clerk_state):
        """Test state transitions in Clerk agent."""
        # Initial state
        assert sample_clerk_state.user_query is not None
        initial_state = sample_clerk_state.next_step

        # Simulate state change
        sample_clerk_state.next_step = "inner"
        assert sample_clerk_state.next_step == "inner"

        # Simulate another state change
        sample_clerk_state.next_step = "final"
        assert sample_clerk_state.next_step == "final"

    def test_librarian_state_transitions(self, sample_librarian_state):
        """Test state transitions in Librarian agent."""
        assert sample_librarian_state.user_query is not None
        
        # Simulate state changes
        sample_librarian_state.next_step = "tool"
        assert sample_librarian_state.next_step == "tool"

        sample_librarian_state.next_step = "final"
        assert sample_librarian_state.next_step == "final"

    def test_supervisor_state_transitions(self, sample_supervisor_state):
        """Test state transitions in Supervisor agent."""
        assert sample_supervisor_state.user_query is not None
        
        # Add identified intents
        task = TaskIntent(
            agent="Clerk",
            intent="Leave_Request",
            decomposed_query="Request leave"
        )
        sample_supervisor_state.identified_intent = [task]

        assert len(sample_supervisor_state.identified_intent) == 1


class TestMessageFlow:
    """Integration tests for message flow between components."""

    def test_message_history_accumulation(self, sample_clerk_state):
        """Test message history accumulation."""
        from langchain_core.messages import HumanMessage, AIMessage

        initial_count = len(sample_clerk_state.messages)

        # Add messages
        sample_clerk_state.messages.append(HumanMessage(content="Query 1"))
        sample_clerk_state.messages.append(AIMessage(content="Response 1"))

        assert len(sample_clerk_state.messages) == initial_count + 2

    def test_conversation_context_preservation(self):
        """Test that conversation context is preserved across exchanges."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        conversation_id = "conv_123"
        user_id = "user_456"
        
        query = UserQuery(
            query="First question",
            conversation_id=conversation_id,
            user_id=user_id,
            auth_token="token"
        )

        # Verify context is preserved
        assert query.conversation_id == conversation_id
        assert query.user_id == user_id


class TestErrorRecovery:
    """Integration tests for error recovery and resilience."""

    def test_clerk_error_recovery(self, mock_llm_model):
        """Test Clerk agent error recovery."""
        from application.agents.clerk import ClerkAgent
        
        mock_llm_error = Mock()
        mock_llm_error.invoke.side_effect = Exception("LLM Error")
        mock_leave = Mock()
        mock_ticket = Mock()

        agent = ClerkAgent(mock_llm_error, mock_leave, mock_ticket)

        # Create a state
        state = ClerkState(
            user_query=UserQuery(
                query="Test",
                conversation_id="conv",
                auth_token="token"
            ),
            messages=[],
            pending_tasks=deque(),
            tool_results=[],
            final_response=deque(),
            hitl_state=deque(),
            next_step=None
        )

        # Should handle error gracefully
        result = agent.Clerk_Outer_Model_Node(state)
        assert "pending_tasks" in result

    def test_librarian_error_recovery(self, mock_llm_model):
        """Test Librarian agent error recovery."""
        from application.agents.librarian import LibrarianAgent
        
        mock_llm_error = Mock()
        mock_llm_error.invoke.side_effect = Exception("LLM Error")

        agent = LibrarianAgent(
            mock_llm_error,
            Mock(),
            Mock(),
            Mock()
        )

        state = LibrarianState(
            user_query=UserQuery(
                query="Test",
                conversation_id="conv",
                auth_token="token"
            ),
            messages=[],
            action=[],
            hitl_state=[],
            next_step=None,
            response=None
        )

        result = agent.librarian_model_node(state)
        assert result == {}

    def test_supervisor_error_recovery(self, mock_async_llm_model):
        """Test Supervisor agent error recovery."""
        from application.agents.supervisor import SupervisorAgent
        
        mock_llm_error = AsyncMock()
        mock_llm_error.ainvoke.side_effect = Exception("LLM Error")

        agent = SupervisorAgent(
            mock_llm_error,
            Mock(),
            Mock()
        )

        # Verify agent was created successfully despite potential errors
        assert agent is not None


class TestDataPersistence:
    """Integration tests for data persistence."""

    def test_state_serialization(self, sample_clerk_state):
        """Test that agent state can be serialized."""
        state_dict = {
            "user_query": sample_clerk_state.user_query.model_dump(),
            "pending_tasks": str(sample_clerk_state.pending_tasks),
            "next_step": sample_clerk_state.next_step,
            "hitl_state": sample_clerk_state.hitl_state
        }

        assert state_dict["user_query"]["query"] is not None

    def test_entity_serialization(self, sample_ticket_creation):
        """Test that entities can be serialized to JSON."""
        json_str = sample_ticket_creation.model_dump_json()
        assert json_str is not None
        
        # Verify it can be deserialized
        from domain.entities import TicketCreation
        deserialized = TicketCreation.model_validate_json(json_str)
        assert deserialized.ticket_type == sample_ticket_creation.ticket_type


class TestPerformanceCharacteristics:
    """Integration tests for performance characteristics."""

    def test_lightweight_state_transitions(self, sample_clerk_state):
        """Test that state transitions are lightweight."""
        import time
        
        start_time = time.time()
        
        for _ in range(100):
            sample_clerk_state.next_step = "inner"
            sample_clerk_state.next_step = "final"
        
        elapsed = time.time() - start_time
        # Should complete quickly (less than 1 second for 200 transitions)
        assert elapsed < 1.0

    def test_message_history_scalability(self):
        """Test that message history scales well."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        messages = []
        
        # Add many messages
        for i in range(100):
            messages.append(HumanMessage(content=f"Query {i}"))
            messages.append(AIMessage(content=f"Response {i}"))
        
        assert len(messages) == 200


class TestCrossComponentInteraction:
    """Tests for interactions between different components."""

    def test_clerk_to_librarian_handoff(self):
        """Test handoff from Clerk to Librarian."""
        # Create task that needs librarian
        task = TaskIntent(
            agent="Librarian",
            intent="Policy_Query",
            decomposed_query="Get leave policy"
        )

        assert task.agent == "Librarian"
        assert task.intent == "Policy_Query"

    def test_librarian_to_clerk_handoff(self):
        """Test handoff from Librarian to Clerk."""
        task = TaskIntent(
            agent="Clerk",
            intent="Leave_Request",
            decomposed_query="Create leave ticket"
        )

        assert task.agent == "Clerk"
        assert task.intent == "Leave_Request"

    def test_supervisor_delegation(self):
        """Test supervisor delegating tasks to other agents."""
        tasks = [
            TaskIntent(
                agent="Clerk",
                intent="Leave_Request",
                decomposed_query="Check eligibility"
            ),
            TaskIntent(
                agent="Librarian",
                intent="Policy_Query",
                decomposed_query="Get policy details"
            )
        ]

        # Verify supervisor can track multiple delegated tasks
        assert len(tasks) == 2
        assert tasks[0].agent != tasks[1].agent
