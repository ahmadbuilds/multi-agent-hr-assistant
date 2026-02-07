from pydantic import BaseModel,Field
from domain.intents import IntentType,TicketType,TicketStatusType,ClerkActionType,AgentName
from typing import Optional
#pydantic model to represent user query
class UserQuery(BaseModel):
    query:str=Field(description="query string from the user which needs to be answered")
    UploadedText:Optional[str]=Field(description="optional text uploaded by the user to provide context to the query",default="")
    isAdmin:Optional[bool]=Field(description="boolean flag to indicate the Manipulation of Policy Documents", default=None)


#pydantic model for Supervisor Structured Output
class Supervisor_structured_output(BaseModel):
    summary:str=Field(description="summary of the supervisor's analysis of the intent and routing decision")
    intent:IntentType=Field(description="identified intent from the user query")

#pydantic model for Creating Ticket
class TicketCreation(BaseModel):
    ticket_type:TicketType=Field(description="type of ticket to be created")
    subject:str=Field(description="subject of the ticket")
    description:str=Field(description="detailed description of the ticket")
    status:TicketStatusType=Field(description="current status of the ticket",default="in_progress")
    leave_days:Optional[int]=Field(description="number of leave days requested, applicable only for leave tickets",default=None)

#pydantic model for Clerk Classification
class ClerkClassificationState(BaseModel):
    action:ClerkActionType
    details: Optional[dict]=None

#pydantic model for Multiple Tasks output of Clerk Agent
class ClerkMultipleTasksOutput(BaseModel):
    tasks:list[ClerkClassificationState]=Field(description="list of classified tasks by the Clerk Agent in structured format")

#pydantic model for Saving state of Agent on Redis Server
class AgentState(BaseModel):
    user_id:str=Field(description="unique identifier for the user associated with this agent state")
    key:str=Field(description="unique key to identify the agent state in Redis")
    state:dict=Field(description="state of the agent to be saved in Redis")