from pydantic import BaseModel,Field

#pydantic model to represent user query
class UserQuery(BaseModel):
    query:str=Field(description="query string from the user which needs to be answered")
    isUploaded:bool=Field(description="boolean flag to indicate if the user has uploaded any document or not")