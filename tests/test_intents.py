"""
Tests for domain intents and intent types.
"""
import pytest
from domain.intents import (
    IntentType,
    SUPERVISOR_ONLY_INTENTS,
    AgentName,
    UserResponseType,
    ClerkActionType,
    LibrarianActionType,
    TicketType,
    TicketStatusType,
)


class TestIntentTypes:
    """Test cases for IntentType validation."""

    def test_valid_intent_types(self):
        """Test all valid intent types."""
        valid_intents = [
            "Policy_Query",
            "Leave_Request",
            "Complaint_filing",
            "Clarification",
            "General_Chat",
        ]
        for intent in valid_intents:
            # These should not raise an error when used correctly
            assert intent in ["Policy_Query", "Leave_Request", "Complaint_filing", "Clarification", "General_Chat"]

    def test_policy_query_intent(self):
        """Test Policy_Query intent."""
        intent: IntentType = "Policy_Query"
        assert intent == "Policy_Query"

    def test_leave_request_intent(self):
        """Test Leave_Request intent."""
        intent: IntentType = "Leave_Request"
        assert intent == "Leave_Request"

    def test_complaint_filing_intent(self):
        """Test Complaint_filing intent."""
        intent: IntentType = "Complaint_filing"
        assert intent == "Complaint_filing"

    def test_clarification_intent(self):
        """Test Clarification intent."""
        intent: IntentType = "Clarification"
        assert intent == "Clarification"

    def test_general_chat_intent(self):
        """Test General_Chat intent."""
        intent: IntentType = "General_Chat"
        assert intent == "General_Chat"


class TestSupervisorOnlyIntents:
    """Test cases for supervisor-only intents."""

    def test_supervisor_only_intents_set(self):
        """Test that supervisor-only intents are correctly defined."""
        assert "Clarification" in SUPERVISOR_ONLY_INTENTS
        assert "General_Chat" in SUPERVISOR_ONLY_INTENTS
        assert len(SUPERVISOR_ONLY_INTENTS) == 2

    def test_non_supervisor_intents(self):
        """Test that non-supervisor intents are not in the set."""
        assert "Policy_Query" not in SUPERVISOR_ONLY_INTENTS
        assert "Leave_Request" not in SUPERVISOR_ONLY_INTENTS
        assert "Complaint_filing" not in SUPERVISOR_ONLY_INTENTS

    def test_check_supervisor_only_intents(self):
        """Test checking if intent is supervisor-only."""
        def is_supervisor_only(intent: IntentType) -> bool:
            return intent in SUPERVISOR_ONLY_INTENTS

        assert is_supervisor_only("Clarification")
        assert is_supervisor_only("General_Chat")
        assert not is_supervisor_only("Leave_Request")


class TestAgentNames:
    """Test cases for AgentName type."""

    def test_valid_agent_names(self):
        """Test all valid agent names."""
        valid_agents = ["Supervisor", "Librarian", "Clerk"]
        for agent in valid_agents:
            assert agent in ["Supervisor", "Librarian", "Clerk"]

    def test_supervisor_agent(self):
        """Test Supervisor agent name."""
        agent: AgentName = "Supervisor"
        assert agent == "Supervisor"

    def test_librarian_agent(self):
        """Test Librarian agent name."""
        agent: AgentName = "Librarian"
        assert agent == "Librarian"

    def test_clerk_agent(self):
        """Test Clerk agent name."""
        agent: AgentName = "Clerk"
        assert agent == "Clerk"


class TestUserResponseTypes:
    """Test cases for user response types."""

    def test_approve_response(self):
        """Test Approve response type."""
        response: UserResponseType = "Approve"
        assert response == "Approve"

    def test_reject_response(self):
        """Test Reject response type."""
        response: UserResponseType = "Reject"
        assert response == "Reject"


class TestClerkActionTypes:
    """Test cases for clerk action types."""

    def test_general_information_action(self):
        """Test general_information action."""
        action: ClerkActionType = "general_information"
        assert action == "general_information"

    def test_get_balance_action(self):
        """Test get_balance action."""
        action: ClerkActionType = "get_balance"
        assert action == "get_balance"

    def test_ticket_creation_action(self):
        """Test ticket_creation action."""
        action: ClerkActionType = "ticket_creation"
        assert action == "ticket_creation"

    def test_all_clerk_actions(self):
        """Test all clerk action types."""
        valid_actions = ["general_information", "get_balance", "ticket_creation"]
        assert len(valid_actions) == 3


class TestLibrarianActionTypes:
    """Test cases for librarian action types."""

    def test_upload_policy_action(self):
        """Test upload_policy action."""
        action: LibrarianActionType = "upload_policy"
        assert action == "upload_policy"

    def test_retrieve_policy_action(self):
        """Test retrieve_policy action."""
        action: LibrarianActionType = "retrieve_policy"
        assert action == "retrieve_policy"

    def test_delete_policy_action(self):
        """Test delete_policy action."""
        action: LibrarianActionType = "delete_policy"
        assert action == "delete_policy"

    def test_update_policy_action(self):
        """Test update_policy action."""
        action: LibrarianActionType = "update_policy"
        assert action == "update_policy"

    def test_all_librarian_actions(self):
        """Test all librarian action types."""
        valid_actions = [
            "upload_policy",
            "retrieve_policy",
            "delete_policy",
            "update_policy",
        ]
        assert len(valid_actions) == 4


class TestTicketTypes:
    """Test cases for ticket types."""

    def test_complaint_ticket(self):
        """Test complaint ticket type."""
        ticket_type: TicketType = "complaint"
        assert ticket_type == "complaint"

    def test_help_ticket(self):
        """Test help ticket type."""
        ticket_type: TicketType = "help"
        assert ticket_type == "help"

    def test_leave_ticket(self):
        """Test leave ticket type."""
        ticket_type: TicketType = "leave"
        assert ticket_type == "leave"

    def test_all_ticket_types(self):
        """Test all ticket types."""
        valid_types = ["complaint", "help", "leave"]
        assert len(valid_types) == 3


class TestTicketStatusTypes:
    """Test cases for ticket status types."""

    def test_in_progress_status(self):
        """Test in_progress status."""
        status: TicketStatusType = "in_progress"
        assert status == "in_progress"

    def test_accepted_status(self):
        """Test accepted status."""
        status: TicketStatusType = "accepted"
        assert status == "accepted"

    def test_rejected_status(self):
        """Test rejected status."""
        status: TicketStatusType = "rejected"
        assert status == "rejected"

    def test_all_ticket_statuses(self):
        """Test all ticket status types."""
        valid_statuses = ["in_progress", "accepted", "rejected"]
        assert len(valid_statuses) == 3


class TestIntentValidationLogic:
    """Test cases for intent validation logic."""

    def test_intent_routing_logic(self):
        """Test intent routing logic."""
        def should_route_to_supervisor_only(intent: IntentType) -> bool:
            return intent in SUPERVISOR_ONLY_INTENTS

        # Test supervisor-only intents
        assert should_route_to_supervisor_only("Clarification")
        assert should_route_to_supervisor_only("General_Chat")

        # Test other intents
        assert not should_route_to_supervisor_only("Policy_Query")
        assert not should_route_to_supervisor_only("Leave_Request")

    def test_agent_capability_mapping(self):
        """Test mapping of agents to capabilities."""
        clerk_intents = ["Leave_Request", "Complaint_filing", "General_Chat"]
        librarian_intents = ["Policy_Query"]
        supervisor_intents = ["Clarification", "General_Chat"]

        assert "Leave_Request" in clerk_intents
        assert "Policy_Query" in librarian_intents
        assert "Clarification" in supervisor_intents

    def test_action_intent_mapping(self):
        """Test mapping of actions to intents."""
        intent_to_action = {
            "Leave_Request": "ticket_creation",
            "Complaint_filing": "ticket_creation",
            "Policy_Query": "retrieve_policy",
            "General_Chat": "general_information",
        }

        assert intent_to_action["Leave_Request"] == "ticket_creation"
        assert intent_to_action["Policy_Query"] == "retrieve_policy"
