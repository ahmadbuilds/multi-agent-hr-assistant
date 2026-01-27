from pydantic import BaseModel,Field
from domain.entities import IntentType
#pydantic model to represent user query
class UserQuery(BaseModel):
    query:str=Field(description="query string from the user which needs to be answered")
    UploadedText:str=Field(description="optional text uploaded by the user to provide context to the query",default="")
    isAdmin:bool=Field(description="boolean flag to indicate the Manipulation of Policy Documents")


#pydantic model for Supervisor Structured Output
class Supervisor_structured_output(BaseModel):
    summary:str=Field(description="summary of the supervisor's analysis of the intent and routing decision")
    intent:IntentType=Field(description="identified intent from the user query")