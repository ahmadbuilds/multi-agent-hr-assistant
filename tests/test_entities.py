"""
Tests for domain entities and data models.
"""
import pytest
from pydantic import ValidationError

from domain.entities import (
    UserQuery,
    TicketCreation,
    Supervisor_structured_output,
    TicketCreationClassification,
    GetBalanceClassification,
    GeneralInformationClassification,
    GeneralInformationResponse,
    ClerkMultipleTasksOutput,
    AgentState,
    TaskIntent,
    SupervisorTaskIntent,
    LibrarianTask,
    LibrarianTaskIntent,
)
from domain.intents import IntentType, TicketType, AgentName


class TestUserQuery:
    """Test cases for UserQuery entity."""

    def test_user_query_creation(self, sample_user_query):
        """Test successful UserQuery creation."""
        assert sample_user_query.query == "I need to request leave for 5 days"
        assert sample_user_query.conversation_id == "conv_123"
        assert sample_user_query.user_id == "user_456"
        assert sample_user_query.auth_token == "token_xyz"
        assert sample_user_query.isAdmin is False

    def test_user_query_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            UserQuery(conversation_id="conv_123", auth_token="token_xyz")

    def test_user_query_with_attachment(self):
        """Test UserQuery with attachment details."""
        query = UserQuery(
            query="Check policy on remote work",
            conversation_id="conv_123",
            auth_token="token_xyz",
            attachment_url="https://example.com/policy.pdf",
            attachment_name="remote_work_policy.pdf"
        )
        assert query.attachment_url == "https://example.com/policy.pdf"
        assert query.attachment_name == "remote_work_policy.pdf"

    def test_user_query_with_uploaded_text(self):
        """Test UserQuery with uploaded text."""
        uploaded_text = "Company policies regarding leave management"
        query = UserQuery(
            query="Summarize this policy",
            conversation_id="conv_123",
            auth_token="token_xyz",
            UploadedText=uploaded_text
        )
        assert query.UploadedText == uploaded_text

    def test_user_query_admin_flag(self):
        """Test UserQuery with admin flag."""
        query = UserQuery(
            query="Update leave policy",
            conversation_id="conv_123",
            auth_token="token_xyz",
            isAdmin=True
        )
        assert query.isAdmin is True


class TestTicketCreation:
    """Test cases for TicketCreation entity."""

    def test_ticket_creation(self, sample_ticket_creation):
        """Test successful TicketCreation."""
        assert sample_ticket_creation.ticket_type == "leave"
        assert sample_ticket_creation.subject == "Leave Request"
        assert sample_ticket_creation.leave_days == 5
        assert sample_ticket_creation.status == "in_progress"

    def test_ticket_creation_complaint(self):
        """Test TicketCreation for complaint type."""
        ticket = TicketCreation(
            ticket_type="complaint",
            subject="Workplace Issue",
            description="There is a workplace issue to report"
        )
        assert ticket.ticket_type == "complaint"

    def test_ticket_creation_help(self):
        """Test TicketCreation for help type."""
        ticket = TicketCreation(
            ticket_type="help",
            subject="Need Help",
            description="I need assistance with my benefits"
        )
        assert ticket.ticket_type == "help"

    def test_ticket_creation_invalid_type(self):
        """Test TicketCreation with invalid ticket type."""
        with pytest.raises(ValidationError):
            TicketCreation(
                ticket_type="invalid",
                subject="Test",
                description="Test description"
            )

    def test_ticket_creation_leave_with_days(self):
        """Test TicketCreation for leave with duration."""
        ticket = TicketCreation(
            ticket_type="leave",
            subject="Leave Request",
            description="Requesting leave for vacation",
            leave_days=10,
            accepted=False
        )
        assert ticket.leave_days == 10
        assert ticket.accepted is False


class TestClassifications:
    """Test cases for classification entities."""

    def test_ticket_creation_classification(self, sample_ticket_creation):
        """Test TicketCreationClassification."""
        classification = TicketCreationClassification(
            action="ticket_creation",
            details=sample_ticket_creation
        )
        assert classification.action == "ticket_creation"
        assert classification.details.ticket_type == "leave"

    def test_get_balance_classification(self):
        """Test GetBalanceClassification."""
        classification = GetBalanceClassification(
            action="get_balance"
        )
        assert classification.action == "get_balance"

    def test_general_information_classification(self):
        """Test GeneralInformationClassification."""
        response = GeneralInformationResponse(
            response="Leave can be requested for up to 30 days per year"
        )
        classification = GeneralInformationClassification(
            action="general_information",
            details=response
        )
        assert classification.action == "general_information"
        assert "30 days" in classification.details.response


class TestAgentState:
    """Test cases for AgentState entity."""

    def test_agent_state_creation(self):
        """Test AgentState creation."""
        state_data = {
            "pending_tasks": ["task1", "task2"],
            "messages": []
        }
        agent_state = AgentState(
            user_id="user_456",
            key="state_key_123",
            agent_name="Clerk",
            state=state_data
        )
        assert agent_state.user_id == "user_456"
        assert agent_state.agent_name == "Clerk"
        assert agent_state.state["pending_tasks"] == ["task1", "task2"]

    def test_agent_state_librarian(self):
        """Test AgentState for Librarian agent."""
        agent_state = AgentState(
            user_id="user_456",
            key="state_key_456",
            agent_name="Librarian",
            state={}
        )
        assert agent_state.agent_name == "Librarian"


class TestTaskIntent:
    """Test cases for TaskIntent entity."""

    def test_task_intent_creation(self):
        """Test TaskIntent creation."""
        task = TaskIntent(
            agent="Clerk",
            intent="Leave_Request",
            decomposed_query="Request 5 days of leave"
        )
        assert task.agent == "Clerk"
        assert task.intent == "Leave_Request"
        assert task.status == "pending"

    def test_task_intent_with_result(self):
        """Test TaskIntent with execution result."""
        task = TaskIntent(
            agent="Librarian",
            intent="Policy_Query",
            decomposed_query="Find leave policy",
            status="completed",
            result="Leave policy document retrieved successfully"
        )
        assert task.status == "completed"
        assert task.result is not None


class TestSupervisorTaskIntent:
    """Test cases for SupervisorTaskIntent entity."""

    def test_supervisor_task_intent_single_task(self):
        """Test SupervisorTaskIntent with single task."""
        task = TaskIntent(
            agent="Clerk",
            intent="Leave_Request",
            decomposed_query="Request leave"
        )
        supervisor_intent = SupervisorTaskIntent(task=[task])
        assert len(supervisor_intent.task) == 1

    def test_supervisor_task_intent_multiple_tasks(self):
        """Test SupervisorTaskIntent with multiple tasks."""
        tasks = [
            TaskIntent(
                agent="Clerk",
                intent="Leave_Request",
                decomposed_query="Check leave eligibility"
            ),
            TaskIntent(
                agent="Librarian",
                intent="Policy_Query",
                decomposed_query="Get leave policy"
            )
        ]
        supervisor_intent = SupervisorTaskIntent(task=tasks)
        assert len(supervisor_intent.task) == 2


class TestLibrarianTask:
    """Test cases for LibrarianTask entity."""

    def test_librarian_task_retrieve(self):
        """Test LibrarianTask for retrieve action."""
        task = LibrarianTask(
            action="retrieve_policy",
            query="Get leave management policy"
        )
        assert task.action == "retrieve_policy"
        assert task.status == "pending"

    def test_librarian_task_upload(self):
        """Test LibrarianTask for upload action."""
        task = LibrarianTask(
            action="upload_policy",
            query="Upload new leave policy document"
        )
        assert task.action == "upload_policy"

    def test_librarian_task_with_result(self):
        """Test LibrarianTask with completion result."""
        task = LibrarianTask(
            action="retrieve_policy",
            query="Get policy",
            status="completed",
            result="Policy document: Leave Management Policy v2.0"
        )
        assert task.status == "completed"
        assert task.result is not None


class TestLibrarianTaskIntent:
    """Test cases for LibrarianTaskIntent entity."""

    def test_librarian_task_intent_multiple_tasks(self):
        """Test LibrarianTaskIntent with multiple tasks."""
        tasks = [
            LibrarianTask(
                action="retrieve_policy",
                query="Get leave policy"
            ),
            LibrarianTask(
                action="retrieve_policy",
                query="Get complaint policy"
            )
        ]
        task_intent = LibrarianTaskIntent(task=tasks)
        assert len(task_intent.task) == 2


class TestSupervisorStructuredOutput:
    """Test cases for Supervisor_structured_output entity."""

    def test_supervisor_structured_output(self):
        """Test Supervisor_structured_output creation."""
        output = Supervisor_structured_output(
            summary="User is requesting leave",
            intent="Leave_Request"
        )
        assert output.summary == "User is requesting leave"
        assert output.intent == "Leave_Request"


class TestClerkMultipleTasksOutput:
    """Test cases for ClerkMultipleTasksOutput entity."""

    def test_clerk_multiple_tasks_output(self, sample_ticket_creation):
        """Test ClerkMultipleTasksOutput with multiple classifications."""
        classifications = [
            GetBalanceClassification(action="get_balance"),
            TicketCreationClassification(
                action="ticket_creation",
                details=sample_ticket_creation
            )
        ]
        output = ClerkMultipleTasksOutput(tasks=classifications)
        assert len(output.tasks) == 2
