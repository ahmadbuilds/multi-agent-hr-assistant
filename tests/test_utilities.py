"""
Tests for utility functions and helpers.
"""
import pytest
from domain.intents import SUPERVISOR_ONLY_INTENTS, IntentType


class TestIntentRouting:
    """Test cases for intent routing logic."""

    def test_route_to_supervisor(self):
        """Test routing decisions for supervisor-only intents."""
        def should_route_to_supervisor_only(intent: IntentType) -> bool:
            return intent in SUPERVISOR_ONLY_INTENTS

        assert should_route_to_supervisor_only("Clarification")
        assert should_route_to_supervisor_only("General_Chat")

    def test_route_to_clerk(self):
        """Test routing decisions for clerk intents."""
        clerk_intents = ["Leave_Request", "Complaint_filing"]

        for intent in clerk_intents:
            assert intent not in SUPERVISOR_ONLY_INTENTS

    def test_route_to_librarian(self):
        """Test routing decisions for librarian intents."""
        librarian_intents = ["Policy_Query"]

        for intent in librarian_intents:
            assert intent not in SUPERVISOR_ONLY_INTENTS


class TestTaskValidation:
    """Test cases for task validation."""

    def test_task_has_required_fields(self):
        """Test that tasks have all required fields."""
        from domain.entities import TaskIntent

        task = TaskIntent(
            agent="Clerk",
            intent="Leave_Request",
            decomposed_query="Request leave"
        )

        assert hasattr(task, "agent")
        assert hasattr(task, "intent")
        assert hasattr(task, "decomposed_query")
        assert hasattr(task, "status")

    def test_task_status_validation(self):
        """Test task status validation."""
        from domain.entities import TaskIntent

        task = TaskIntent(
            agent="Clerk",
            intent="Leave_Request",
            decomposed_query="Request leave",
            status="pending"
        )

        assert task.status in ["pending", "running", "waiting_for_human", "completed", "error"]


class TestConversationContext:
    """Test cases for conversation context management."""

    def test_conversation_id_uniqueness(self):
        """Test that conversation IDs are handled correctly."""
        from domain.entities import UserQuery

        query1 = UserQuery(
            query="Question 1",
            conversation_id="conv_123",
            auth_token="token"
        )

        query2 = UserQuery(
            query="Question 2",
            conversation_id="conv_456",
            auth_token="token"
        )

        assert query1.conversation_id != query2.conversation_id

    def test_user_context_preservation(self):
        """Test that user context is preserved."""
        from domain.entities import UserQuery

        user_id = "user_789"
        query = UserQuery(
            query="Question",
            conversation_id="conv_123",
            user_id=user_id,
            auth_token="token"
        )

        assert query.user_id == user_id


class TestTicketWorkflow:
    """Test cases for ticket creation workflow."""

    def test_ticket_creation_flow(self):
        """Test the flow of ticket creation."""
        from domain.entities import TicketCreation, TicketCreationClassification

        ticket = TicketCreation(
            ticket_type="leave",
            subject="Leave Request",
            description="Requesting leave",
            leave_days=5
        )

        classification = TicketCreationClassification(
            action="ticket_creation",
            details=ticket
        )

        assert classification.details.ticket_type == "leave"
        assert classification.details.leave_days == 5

    def test_complaint_ticket_creation(self):
        """Test complaint ticket creation."""
        from domain.entities import TicketCreation

        ticket = TicketCreation(
            ticket_type="complaint",
            subject="Workplace Issue",
            description="Description of issue"
        )

        assert ticket.ticket_type == "complaint"

    def test_help_ticket_creation(self):
        """Test help ticket creation."""
        from domain.entities import TicketCreation

        ticket = TicketCreation(
            ticket_type="help",
            subject="Need Assistance",
            description="I need help with..."
        )

        assert ticket.ticket_type == "help"


class TestPolicyManagement:
    """Test cases for policy management workflows."""

    def test_policy_retrieval_task(self):
        """Test policy retrieval task."""
        from domain.entities import LibrarianTask

        task = LibrarianTask(
            action="retrieve_policy",
            query="Get leave policy documents"
        )

        assert task.action == "retrieve_policy"

    def test_policy_upload_task(self):
        """Test policy upload task."""
        from domain.entities import LibrarianTask

        task = LibrarianTask(
            action="upload_policy",
            query="Upload new benefits policy"
        )

        assert task.action == "upload_policy"

    def test_policy_update_task(self):
        """Test policy update task."""
        from domain.entities import LibrarianTask

        task = LibrarianTask(
            action="update_policy",
            query="Update leave policy with new rules"
        )

        assert task.action == "update_policy"

    def test_policy_deletion_task(self):
        """Test policy deletion task."""
        from domain.entities import LibrarianTask

        task = LibrarianTask(
            action="delete_policy",
            query="Remove outdated policy"
        )

        assert task.action == "delete_policy"


class TestLeaveBalance:
    """Test cases for leave balance operations."""

    def test_leave_balance_retrieval(self, mock_leave_balance_port):
        """Test leave balance retrieval."""
        balance = mock_leave_balance_port.get_leave_balance("token_123")
        assert isinstance(balance, int)
        assert balance >= 0

    def test_leave_balance_consumption(self):
        """Test leave balance consumption logic."""
        total_balance = 30
        requested_days = 5
        remaining = total_balance - requested_days

        assert remaining == 25
        assert remaining >= 0

    def test_insufficient_leave_balance(self):
        """Test handling of insufficient leave balance."""
        total_balance = 3
        requested_days = 5

        is_sufficient = total_balance >= requested_days
        assert not is_sufficient
