from typing import Literal

IntentType=Literal[
    "Policy_Query",
    "Leave_Request",
    "Complaint_filing",
    "Clarification",
    "Unknown",
]

ConfidenceLevel=Literal[
    "low",
    "medium",
    "high",
]

TaskStatus=Literal[
    "new",
    "delegated",
    "waiting",
    "agent_responded",
    "completed",
    "failed",
]

AgentName=Literal[
    "policy_agent",
    "leave_agent",
    "complaint_agent",
    "none"
]

ResponseSource=Literal[
    "Supervisor",
    "agent",
]

UIAction=Literal[
    "show_message",
    "ask_clarification",
    "open_form",
    "trigger_HITL",
    "end_flow",
]