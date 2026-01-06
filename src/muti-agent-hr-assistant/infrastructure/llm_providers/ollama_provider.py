from langchain_ollama import ChatOllama

def create_model_instance(model_name:str="llama3.2:3B",temperature:float=0,total_retries:int=3):
    return ChatOllama(
        model=model_name,
        temperature=temperature,
        max_retries=total_retries,
    )