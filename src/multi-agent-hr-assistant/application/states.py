from typing import Literal, Optional, Optional,Sequence,Annotated,TypedDict
from langchain_core.messages import BaseMessage
from domain.intents import IntentType, AgentName
from domain.entities import UserQuery
from langgraph.graph.message import add_messages
from pydantic import BaseModel
#pydantic model for Supervisor State
class SupervisorState(TypedDict):
    #input variables
    query:UserQuery
    conversation_messages:Annotated[Sequence[BaseMessage],add_messages]

    #Decision-making variables
    intent:IntentType
    active_agent:AgentName

    # Librarian (Agent A) result
    librarian_result: Optional["LibrarianState"]

    # Clerk (Agent B) result
    clerk_result: Optional["ClerkState"]

    # HITL
    hitl_required: bool
    hitl_approved: bool

    #output variables
    final_response:Optional[str]
    summary:Optional[str]


#pydantic model for Librarian State
class LibrarianState(BaseModel):
    #input variables
    retrieved_documents:Sequence[str]
    
    #output variables
    answer:str=""
    references:Sequence[str]
    
    #hallucination flag
    has_context:bool


#pydantic model for Clerk State
class ClerkState(BaseModel):
    #input variables
    action: Literal["get_balance", "file_ticket"]
    
    # optional proposal for the action
    proposal: Optional[str]
    
    #output variables
    executed: bool
    api_response: Optional[dict]
