from typing import Literal

IntentType=Literal[
    "Policy_Query",
    "Leave_Request",
    "Complaint_filing",
    "Clarification",
    "General_Chat",
]

AgentName=Literal[
    "Supervisor",
    "Librarian",
    "Clerk",
]

UserResponseType=Literal[
    "Approve",
    "Reject",
]

ClerkActionType=Literal[
    "general_information",
    "get_balance",
    "ticket_creation",
]

LibrarianActionType=Literal[
    "upload_policy",
    "retrieve_policy",
    "delete_policy",
    "update_policy",
]

TicketType=Literal[
    "complaint",
    "help",
    "leave",
]

TicketStatusType=Literal[
    "in_progress",
    "accepted",
    "rejected",
]