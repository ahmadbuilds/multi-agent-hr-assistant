from typing import Literal

IntentType=Literal[
    "Policy_Query",
    "Leave_Request",
    "Complaint_filing",
    "Clarification",
    "Unknown",
]

AgentName=Literal[
    "Supervisor",
    "Librarian",
    "Clerk",
]