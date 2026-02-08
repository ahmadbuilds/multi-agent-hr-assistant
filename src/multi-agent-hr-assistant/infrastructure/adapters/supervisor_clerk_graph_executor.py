from domain.ports import ClerkGraphExecutionPort
from application.states import ClerkState
from application.agents.clerk import ClerkAgent
from infrastructure.llm_providers.ollama_provider import create_model_instance
from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter
from infrastructure.redis.redis_client import save_agent_state
from domain.entities import AgentState
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
            
            #Agent State to be saved in Redis before execution
            agent_state=AgentState(
                user_id=self.clerk_state.user_query.user_id,
                key=self.clerk_state.user_query.conversation_id,
                state={
                    "status":"initialized",
                    "final_response":"",
                    "error":None
                }
            )

            #calling the Redis function to save the initial state of the Clerk Agent before execution
            save_agent_state(agent_state)

            agent_state.state["status"]="running"
            save_agent_state(agent_state)

            #Executing the Clerk Agent Graph
            clerk_graph.execute()

            agent_state.state["status"]="completed"
            save_agent_state(agent_state)
        except Exception as e:
            if agent_state:
                agent_state.state["status"]="error"
                agent_state.state["error"]=str(e)
                save_agent_state(agent_state)
            raise RuntimeError(f"Failed to execute Clerk Agent Graph: {str(e)}")