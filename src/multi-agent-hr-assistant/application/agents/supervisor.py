from langchain_core.messages import AIMessage
from application.states import SupervisorState
from infrastructure.llm_providers.ollama_provider import create_model_instance
from domain.prompts.supervisor_prompt import prompt

def Supervisor_model_node(state:SupervisorState)->SupervisorState:
    query=state.user_message.content
    model=create_model_instance()
    response=model.generate_message(
        messages=[
            prompt,
            AIMessage(content=f"User Query: {query}")
        ]
    )