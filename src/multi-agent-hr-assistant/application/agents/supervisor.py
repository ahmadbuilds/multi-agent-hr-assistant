from langgraph.graph import StateGraph,START,END
from domain.prompts.supervisor_prompt import SupervisorDecompositionPrompt,SupervisorFinalResponsePrompt,GENERAL_CHAT_SYSTEM_PROMPT
from domain.tools.supervisor_tool import make_supervisor_execute_clerk_graph_tool, make_supervisor_execute_librarian_graph_tool
from application.states import LibrarianState, SupervisorState,ClerkState
from langchain_core.language_models.chat_models import BaseChatModel
from infrastructure.redis.redis_client import get_agent_state_for_final_response
from domain.entities import SupervisorTaskIntent, TaskIntent
from langchain_core.messages import AIMessage, HumanMessage
from domain.intents import SUPERVISOR_ONLY_INTENTS
from domain.ports import ClerkGraphExecutionPort, LibrarianGraphExecutionPort
import json
try:
    from IPython.display import Image,display
except ImportError:
    Image=None
    display=None

#Supervisor Agent Implementation
class SupervisorAgent:
    def __init__(self,llm_model:BaseChatModel,SupervisorClerkGraphExecutorPort:ClerkGraphExecutionPort,SupervisorLibrarianGraphExecutorPort:LibrarianGraphExecutionPort):
        self.llm_model=llm_model
        self.SupervisorClerkGraphExecutorPort=SupervisorClerkGraphExecutorPort
        self.SupervisorLibrarianGraphExecutorPort=SupervisorLibrarianGraphExecutorPort
    
    async def decompose_query_into_tasks(self, state: SupervisorState) -> dict:
        """
        This method takes the user's query and decomposes it into specific tasks with associated intents and agents. 
         It uses a structured output prompt to ensure the response is in a predictable format that can be parsed.
        """
        try:
            formatted_prompt = SupervisorDecompositionPrompt.format_messages(
                query=state.user_query.query,
                isUploaded=state.user_query.UploadedText or "None",
                isAdmin=state.user_query.isAdmin or False
            )

            response = await self.llm_model.ainvoke(formatted_prompt)
            # print(f"[decompose] raw response type : {type(response)}")
            # print(f"[decompose] raw response content: '{response.content}'")
            # print(f"[decompose] response_metadata  : {getattr(response, 'response_metadata', {})}")

            raw = response.content.strip()

            if not raw:
                raise ValueError(
                    "Model returned an empty response. "
                    f"response_metadata={getattr(response, 'response_metadata', {})}"
                )

            if raw.startswith("```"):
                lines = raw.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw = "\n".join(lines).strip()

            parsed = json.loads(raw)
            result = SupervisorTaskIntent(**parsed)

            print(f"[decompose] parsed result: {result}")
            return {
                "messages": [AIMessage(content=response.content)],
                "identified_intent": result.task
            }

        except Exception as e:
            print(f"Structured output failed in decompose_query_into_tasks: {e}")
            fallback_task = TaskIntent(
                agent="Supervisor",
                intent="General_Chat",
                decomposed_query=state.user_query.query,
                status="pending",
                result=None
            )
            return {
                "messages": [],
                "identified_intent": [fallback_task]
            }

    # This decision node checks if there are any pending tasks that need to be executed.
    def Supervisor_decision_node(self,state:SupervisorState)->dict:
        pending_tasks=[intent for intent in state.identified_intent if intent.status=="pending"]
        if not pending_tasks:
            next_steps="result"
        else:
            next_steps="tool_node"
        return {"next_steps": next_steps}

    # This tool node executes the pending tasks by invoking the appropriate tools based on the agent 
    # specified in each task.
    async def Supervisor_tool_node(self,state:SupervisorState)->dict:
        pending_tasks=[intent for intent in state.identified_intent if intent.status=="pending"]

        if not pending_tasks:
            return {}

        tasks=pending_tasks[0]
        tasks.status="running"
        try:
            normalized_agent=(tasks.agent or "").strip().lower()

            if normalized_agent=="supervisor" or tasks.intent in SUPERVISOR_ONLY_INTENTS:
                state.active_agent="Supervisor"

                clean_messages = [
                    GENERAL_CHAT_SYSTEM_PROMPT,
                    HumanMessage(content=tasks.decomposed_query)
                ]
                response=await self.llm_model.ainvoke(clean_messages)
                tasks.status="completed"
                tasks.result=response.content

            elif normalized_agent=="clerk":
                state.active_agent="Clerk"
                updated_query=state.user_query.model_copy(update={"query":tasks.decomposed_query})
                clerk_state=ClerkState(user_query=updated_query)
                self.SupervisorClerkGraphExecutorPort.update_clerk_state(clerk_state)
                clerk_graph_executor=make_supervisor_execute_clerk_graph_tool(self.SupervisorClerkGraphExecutorPort)
                await clerk_graph_executor.ainvoke({})
                clerk_result_state=get_agent_state_for_final_response(state.user_query.user_id,state.user_query.conversation_id,"Clerk")
                tasks.status="completed"
                tasks.result=clerk_result_state.get("final_response","") if clerk_result_state else ""

            elif normalized_agent=="librarian":
                state.active_agent="Librarian"
                updated_query=state.user_query.model_copy(update={"query":tasks.decomposed_query})
                librarian_state=LibrarianState(user_query=updated_query)
                self.SupervisorLibrarianGraphExecutorPort.update_librarian_state(librarian_state)
                librarian_graph_executor=make_supervisor_execute_librarian_graph_tool(self.SupervisorLibrarianGraphExecutorPort)
                await librarian_graph_executor.ainvoke({})
                librarian_result_state=get_agent_state_for_final_response(state.user_query.user_id,state.user_query.conversation_id,"Librarian")
                tasks.status="completed"
                tasks.result=librarian_result_state.get("final_response","") if librarian_result_state else ""

            else:
                raise ValueError(f"Unsupported agent '{tasks.agent}' for intent '{tasks.intent}'")

        except Exception as e:
            print(f"Error in Supervisor_tool_node for intent {tasks.intent}: {e}")
            tasks.status="error"
            tasks.result=str(e)

        return {"identified_intent": state.identified_intent}

    # This result node checks if all tasks are completed and then generates the final response to the user.
    async def Supervisor_result_node(self,state:SupervisorState)->dict:
        try:
            all_tasks = state.identified_intent

            all_supervisor_only = all(
                t.intent in SUPERVISOR_ONLY_INTENTS for t in all_tasks
            )
            if all_supervisor_only:
                direct_response = next(
                    (t.result for t in all_tasks if t.result),
                    "I'm here to help! How can I assist you with HR matters?"
                )
                return {
                    "messages": [AIMessage(content=direct_response)],
                    "final_response": direct_response
                }

            formatted_prompt=SupervisorFinalResponsePrompt.format_messages(
                user_query=state.user_query.query,
                identified_intent=json.dumps([t.model_dump() for t in all_tasks], indent=2)
            )
            response=await self.llm_model.ainvoke(formatted_prompt)
            return {
                "messages":[AIMessage(content=response.content)],
                "final_response":response.content
            }

        except Exception as e:
            print(f"Error in Supervisor_result_node: {e}")
            return {
                "messages":[AIMessage(content="Sorry, I am having trouble generating the final response at the moment.")],
                "final_response":"Sorry, I am having trouble generating the final response at the moment."
            }

    
    def create_supervisor_agent_graph(self)->StateGraph:
        graph=StateGraph(SupervisorState)
        graph.add_node("decompose_query_into_tasks",self.decompose_query_into_tasks)
        graph.add_node("Supervisor_decision_node",self.Supervisor_decision_node)
        graph.add_node("Supervisor_tool_node",self.Supervisor_tool_node)
        graph.add_node("Supervisor_result_node",self.Supervisor_result_node)
        graph.add_edge(START,"decompose_query_into_tasks")
        graph.add_edge("decompose_query_into_tasks","Supervisor_decision_node")
        graph.add_conditional_edges(
            "Supervisor_decision_node",
            lambda state:state.next_steps,{
                "result":"Supervisor_result_node",
                "tool_node":"Supervisor_tool_node"
            }
        )
        graph.add_edge("Supervisor_tool_node","Supervisor_decision_node")
        graph.add_edge("Supervisor_result_node",END)
        return graph.compile()

    def build_supervisor_agent_graph_image(self,agent:StateGraph):
        png_bytes=agent.get_graph(xray=True).draw_mermaid_png()
        with open("supervisor_agent_graph.png", "wb") as f:
            f.write(png_bytes)
        display(Image(png_bytes))