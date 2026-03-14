from domain.ports import ClerkGraphExecutionPort
from application.states import ClerkState
from application.agents.clerk import ClerkAgent
from infrastructure.llm_providers.groq_provider import create_model_instance
from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter
from infrastructure.adapters.clerk_ticket_creation_adapter import ClerkTicketCreationAdapter
from infrastructure.redis.redis_client import get_agent_state_for_final_response, save_agent_state_for_final_response
from domain.entities import AgentState
class SupervisorClerkGraphExecutor(ClerkGraphExecutionPort):
    def __init__(self,state:ClerkState):
        self.clerk_state=state
    

    #function to update the state of clerk
    def update_clerk_state(self,state:ClerkState):
        self.clerk_state=state
    #Method to execute the Clerk Agent State Graph
    async def execute_clerk_agent_graph(self)->bool:
        agent_state=None
        try:
            llm_model=create_model_instance("openai/gpt-oss-20b")
            leave_balance_port=ClerkLeaveBalanceAdapter()
            ticket_creation_port=ClerkTicketCreationAdapter()
            clerk_agent=ClerkAgent(llm_model,leave_balance_port,ticket_creation_port)

            #Creating the Clerk Agent Graph
            clerk_graph=clerk_agent.create_clerk_agent_graph()
            
            #Agent State to be saved in Redis before execution
            agent_state=AgentState(
                user_id=self.clerk_state.user_query.user_id,
                key=self.clerk_state.user_query.conversation_id,
                agent_name="Clerk",
                state={
                    "status":"initialized",
                    "final_response":"",
                    "error":None
                }
            )

            #calling the Redis function to save the initial state of the Clerk Agent before execution
            save_agent_state_for_final_response(agent_state)

            agent_state.state["status"]="running"
            save_agent_state_for_final_response(agent_state)

            #Executing the Clerk Agent Graph
            await clerk_graph.ainvoke(self.clerk_state)

            existing = get_agent_state_for_final_response(
                self.clerk_state.user_query.user_id,
                self.clerk_state.user_query.conversation_id,
                "Clerk"
            )
            agent_state.state = {**existing, "status": "completed"}
            save_agent_state_for_final_response(agent_state)

            return True
        except Exception as e:
            if agent_state:
                agent_state.state["status"]="error"
                agent_state.state["error"]=str(e)
                save_agent_state_for_final_response(agent_state)
            raise RuntimeError(f"Failed to execute Clerk Agent Graph: {str(e)}")