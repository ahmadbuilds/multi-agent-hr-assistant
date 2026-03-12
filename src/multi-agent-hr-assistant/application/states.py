from __future__ import annotations
from typing import Optional, Optional,Sequence,Annotated
from langchain_core.messages import BaseMessage
from domain.intents import IntentType, AgentName, LibrarianActionType, UserResponseType
from domain.entities import ClerkClassificationState, LibrarianTask, TaskIntent, UserQuery
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from collections import deque
from typing import Literal
#pydantic model for Supervisor State
class SupervisorState(BaseModel):
    #General State for Supervisor Agent
    user_query: UserQuery
    messages: Annotated[Sequence[BaseMessage], add_messages] = []

    #Current working agent and identified intent
    active_agent: Optional[AgentName] = "Supervisor"
    identified_intent: list[TaskIntent] = []

    #final response to be sent to the user
    final_response: Optional[str] = None

    #Supervisor next steps
    next_steps:Optional[Literal["result","tool_node"]] = None

#pydantic model for clerk State
class ClerkState(BaseModel):
    #General State for Clerk Agent
    user_query: UserQuery
    messages: Annotated[Sequence[BaseMessage], add_messages] = []

    #Clerk Action to be performed
    pending_tasks:deque[ClerkClassificationState]=deque()

    #Results from tool execution, if any
    tool_results: list[dict | int | bool] = []

    #final response to be returned to the Supervisor
    final_response: deque[ClerkClassificationState] = deque()

    #HITL State for Clerk Agent
    hitl_state:deque[ClerkClassificationState] = deque()

    #next Step for the Clerk Agent to take, can be "clerk_inner_model_node", "hitl_intervention_node" or "final_response_node"
    next_step: Optional[Literal["inner","final","hitl"]] = None

#pydantic model for Librarian State
class LibrarianState(BaseModel):
    #General State for Librarian Agent
    user_query: UserQuery
    messages: Annotated[Sequence[BaseMessage], add_messages] = []

    #Librarian Action to be performed
    action:list[LibrarianTask]=[]

    #librarian HITL state
    hitl_state:list[LibrarianTask]=[]

    #next step for librarian agent
    next_step: Optional[Literal["tool_node","final_response","hitl"]] = None

    #final response to be returned to the Supervisor
    response: Optional[str] = None
