from pydantic import BaseModel,Field
from domain.entities import IntentType
from domain.intents import TicketType,TicketStatusType
from typing import Optional
#pydantic model to represent user query
class UserQuery(BaseModel):
    query:str=Field(description="query string from the user which needs to be answered")
    UploadedText:str=Field(description="optional text uploaded by the user to provide context to the query",default="")
    isAdmin:bool=Field(description="boolean flag to indicate the Manipulation of Policy Documents")


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