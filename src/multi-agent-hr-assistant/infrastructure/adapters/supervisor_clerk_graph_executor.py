from domain.ports import ClerkGraphExecutionPort
from application.states import ClerkState
from application.agents.clerk import ClerkAgent
from infrastructure.llm_providers.ollama_provider import create_model_instance
from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter

class SupervisorClerkGraphExecutor(ClerkGraphExecutionPort):
    def __init__(self,state:ClerkState):
        self.clerk_state=state
    
    #Method to execute the Clerk Agent State Graph
    def execute_clerk_agent_graph(self):
        try:
            llm_model=create_model_instance("mistral:latest")
            leave_balance_port=ClerkLeaveBalanceAdapter()
            clerk_agent=ClerkAgent(llm_model,leave_balance_port)

            #Creating the Clerk Agent Graph
            clerk_graph=clerk_agent.create_clerk_agent_graph(self.clerk_state)
        
            #Executing the Clerk Agent Graph
            clerk_graph.execute()
        except Exception as e:
            print("Error Executing Clerk Agent Graph:", str(e))
            return