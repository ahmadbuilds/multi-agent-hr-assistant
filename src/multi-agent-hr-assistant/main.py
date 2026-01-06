from infrastructure.llm_providers.ollama_provider import create_model_instance

model=create_model_instance()

print(model("Hello").content)