from pydantic import BaseModel,Field
from domain.intents import IntentType, LibrarianActionType,TicketType,TicketStatusType,ClerkActionType,AgentName
from typing import Optional,Literal, Union,TypeAlias
#pydantic model to represent user query
class UserQuery(BaseModel):
    query:str=Field(description="query string from the user which needs to be answered")
    UploadedText:Optional[str]=Field(description="optional text uploaded by the user to provide context to the query",default="")
    isAdmin:Optional[bool]=Field(description="boolean flag to indicate the Manipulation of Policy Documents", default=None)
    conversation_id:str=Field(description="unique identifier for the conversation, used for maintaining context across interactions")
    user_id:Optional[str]=Field(description="unique identifier for the user, used for maintaining context and state across interactions",default=None)
    auth_token:str=Field(description="authentication token for the user, used to verify identity and fetch user details")

#pydantic model for Supervisor Structured Output
class Supervisor_structured_output(BaseModel):
    summary:str=Field(description="summary of the supervisor's analysis of the intent and routing decision")
    intent:IntentType=Field(description="identified intent from the user query")

#pydantic model for Creating Ticket
class TicketCreation(BaseModel):
    ticket_type:TicketType=Field(description="type of ticket to be created")
    subject:str=Field(description="subject of the ticket")
    description:str=Field(description="detailed description of the ticket")
    status:Literal["in_progress"]=Field(description="current status of the ticket",default="in_progress")
    leave_days:Optional[int]=Field(description="number of leave days requested, applicable only for leave tickets",default=None)
    accepted:Optional[bool]=Field(description="flag to indicate if the ticket has been accepted by the user in case of leave request and file complaint",default=None)

#pydantic models for Clerk Classification
class TicketCreationClassification(BaseModel):
    action:Literal["ticket_creation"]=Field(description="action type for ticket creation")
    details:TicketCreation=Field(description="details of the ticket to be created")

class GetBalanceClassification(BaseModel):
    action:Literal["get_balance"]=Field(description="action type for getting balance")
    details:Optional[dict]=Field(description="no details required for get balance action",default=None)

class GeneralInformationResponse(BaseModel):
    response:str=Field(description="response string containing the general information relevant to the user's query")

class GeneralInformationClassification(BaseModel):
    action:Literal["general_information"]=Field(description="action type for general information query")
    details:GeneralInformationResponse=Field(description="details containing the specific informational response relevant to the user's query")

ClerkClassificationState:TypeAlias=Union[
    TicketCreationClassification,
    GetBalanceClassification,
    GeneralInformationClassification
]

#pydantic model for Multiple Tasks output of Clerk Agent
class ClerkMultipleTasksOutput(BaseModel):
    tasks:list[ClerkClassificationState]=Field(description="list of classified tasks by the Clerk Agent in structured format")

#pydantic model for Saving state of Agent on Redis Server
class AgentState(BaseModel):
    user_id:str=Field(description="unique identifier for the user associated with this agent state")
    key:str=Field(description="unique key to identify the agent state in Redis")
    agent_name:Literal["Clerk","Librarian"]=Field(description="name of the agent whose state is being saved")
    state:dict=Field(description="state of the agent to be saved in Redis")
    

#pydantic model for Supervisor to handle multi-intent queries
class TaskIntent(BaseModel):
    agent:AgentName=Field(description="name of the agent responsible for handling this intent")
    intent:IntentType=Field(description="identified intent for this task")
    decomposed_query:str=Field(description="decomposed query for the agent to handle this specific intent")
    status:Literal["pending","running","waiting_for_human","completed","error"]=Field(description="current status of the task",default="pending")
    result:Optional[str]=Field(description="result of the task execution, can contain tool execution results or final response from the agent",default=None)

class SupervisorTaskIntent(BaseModel):
     task:list[TaskIntent]=Field(description="list of identified intents for the Supervisor Agent to handle in structured format")


#pydantic model for librarian agent for getting pending tasks
class LibrarianTask(BaseModel):
    action:LibrarianActionType=Field(description="action to be performed by the Librarian Agent based on the identified intent and routing decision by the Supervisor Agent")
    query:str=Field(description="specific query or instruction for the Librarian Agent to perform the assigned action, can contain details of the document to be retrieved or manipulated and any specific information to be included in the document retrieval or manipulation")
    status:Literal["pending","completed","waiting_for_human","error"]=Field(description="current status of the task assigned to the Librarian Agent",default="pending")
    result:Optional[str]=Field(description="result of the task execution by the Librarian Agent, can contain details of the document retrieved or confirmation of document upload/update/deletion",default=None)
    hitl_response:Optional[bool]=Field(description="flag to indicate if the user has made the confirmation regarding the update policy or not",default=None)

class LibrarianTaskIntent(BaseModel):
    task:list[LibrarianTask]=Field(description="list of tasks assigned to the Librarian Agent in structured format based on the identified intent and routing decision by the Supervisor Agent")