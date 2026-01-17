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