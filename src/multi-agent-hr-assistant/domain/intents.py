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
    "get_balance",
    "file_complaint",
]

LibrarianActionType=Literal[
    "upload_policy",
    "retrieve_policy",
    "delete_policy",
    "update_policy",
]