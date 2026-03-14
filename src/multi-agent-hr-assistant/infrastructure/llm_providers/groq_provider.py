from langchain_groq import ChatGroq

def create_model_instance(model_name:str="meta-llama/llama-4-scout-17b-16e-instruct",temperature:float=0,total_retries:int=3):
    model=ChatGroq(
        model=model_name,
        temperature=temperature,
        max_retries=total_retries,
    )
    return model