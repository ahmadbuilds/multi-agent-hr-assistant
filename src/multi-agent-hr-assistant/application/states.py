from typing import Optional,Literal,Annotated,Sequence
from dataclasses import dataclass
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from domain.entities import UserQuery
from domain.intents import (
    IntentType,
    ConfidenceLevel,
    AgentName,
    TaskStatus,
    ResponseSource,
    UIAction,
)

@dataclass
class SupervisorState:
    #input state
    user_message:UserQuery
    conversation_memory:Annotated[Sequence[BaseMessage],add_messages]

    #intent state
    intent:Optional[IntentType]=None
    intent_confidence:Optional[ConfidenceLevel]=None

    #Routing State
    selected_agent:AgentName="none"
    routing_reason:Optional[str]=None 

    #task status
    status:TaskStatus="new"

    #Agent output state
    agent_response:Optional[str]=None
    agent_validity:Optional[
        Literal["valid","incomplete","irrelevant","unsafe"]
    ]=None

    #final state
    final_response:Optional[str]=None
    response_source:Optional[ResponseSource]=None
    ui_action:Optional[UIAction]=None