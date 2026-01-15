from langchain_ollama import ChatOllama

def create_model_instance(model_name:str="phi3:mini",temperature:float=0,total_retries:int=3):
    model=ChatOllama(
        model=model_name,
        temperature=temperature,
        max_retries=total_retries,
    )
    return model