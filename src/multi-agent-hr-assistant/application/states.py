from __future__ import annotations
from typing import Optional, Optional,Sequence,Annotated
from langchain_core.messages import BaseMessage
from domain.intents import IntentType, AgentName, LibrarianActionType, UserResponseType
from domain.entities import ClerkClassificationState, UserQuery
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
    identified_intent: Optional[IntentType] = None

    #Waiting flag to indicate if the Supervisor is waiting for a response from another agent
    waiting_for_response: bool = False

    #final response to be sent to the user
    final_response: Optional[str] = None
    final_summary: Optional[str] = None

#pydantic model for HITL State
class HITLState(BaseModel):
    #question for the user to answer
    question: str=""
    
    #options for the user to choose from
    options: Sequence[UserResponseType]=[]

    #HITL intervention agent
    agent: AgentName="Supervisor"

    #Counter for attempts made to get user response
    attempts: int=0

    #flag to indicate if waiting for user response
    waiting_for_user: bool = False

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
    action:LibrarianActionType

    #final response to be returned to the Supervisor
    response: Optional[dict] = None
    citation_response: Optional[dict] = None
