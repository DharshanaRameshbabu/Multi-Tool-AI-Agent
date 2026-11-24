import time
from typing import Dict, Any, List, Literal, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.llm import get_llm
from app.tools.registry import ALL_TOOLS, TOOL_MAP
from app.db.database import SessionLocal
from app.db import crud
from app.core.logging import logger
from app.core.config import settings

def create_agent_node(model):
    """Factory to create the agent decision node with tools bound."""
    model_with_tools = model.bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState) -> Dict[str, Any]:
        messages = list(state["messages"])
        
        # Ensure system prompt is prepended if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        logger.info(f"Agent Node invoking LLM with {len(messages)} messages (Iteration {state.get('iteration_count', 0) + 1})")
        response = model_with_tools.invoke(messages)
        
        iteration_count = state.get("iteration_count", 0) + 1
        return {
            "messages": [response],
            "iteration_count": iteration_count
        }

    return agent_node


def tools_node(state: AgentState) -> Dict[str, Any]:
    """
    Executes tool calls requested by the agent, records execution duration,
    and logs the audit trace to SQLite.
    """
    last_message = state["messages"][-1]
    tool_messages: List[ToolMessage] = []
    tool_trace: List[Dict[str, Any]] = list(state.get("tool_calls_trace", []))
    session_id = state.get("session_id", "default_session")

    db = SessionLocal()
    try:
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_name = tc.get("name")
                tool_args = tc.get("args", {})
                tool_id = tc.get("id")

                logger.info(f"Executing Tool '{tool_name}' with args: {tool_args}")
                start_time = time.time()
                status = "Success"
                
                try:
                    target_tool = TOOL_MAP.get(tool_name)
                    if not target_tool:
                        result = f"Error: Tool '{tool_name}' is not registered."
                        status = "Error"
                    else:
                        # Execute the tool
                        result = target_tool.invoke(tool_args)
                except Exception as e:
                    logger.error(f"Error executing tool '{tool_name}': {e}")
                    result = f"Error during tool execution: {str(e)}"
                    status = "Error"

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                
                # Persist to database audit log
                crud.log_tool_execution(
                    db=db,
                    tool_name=tool_name,
                    tool_input=str(tool_args),
                    tool_output=str(result),
                    status=status,
                    execution_time_ms=elapsed_ms,
                    session_id=session_id
                )

                # Record in-memory trace for API and Streamlit UI
                tool_trace.append({
                    "tool_name": tool_name,
                    "tool_input": tool_args,
                    "tool_output": str(result),
                    "status": status.lower(),
                    "execution_time_ms": elapsed_ms
                })

                # Create ToolMessage
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
    finally:
        db.close()

    return {
        "messages": tool_messages,
        "tool_calls_trace": tool_trace
    }


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Conditional router: checks if the agent decided to call tools or finish."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Safety limit to avoid infinite tool loops
    max_iter = settings.MAX_AGENT_ITERATIONS
    if state.get("iteration_count", 0) >= max_iter:
        logger.warning(f"Reached maximum agent iterations ({max_iter}). Halting execution.")
        return END

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        logger.info(f"Agent made {len(last_message.tool_calls)} tool call(s). Routing to 'tools' node.")
        return "tools"
    
    logger.info("Agent produced final response. Ending workflow.")
    return END


# In-memory checkpointer for conversation memory across turns
checkpointer = MemorySaver()

def build_agent_graph(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    use_memory: bool = True
):
    """
    Constructs and compiles the LangGraph state machine.
    """
    llm = get_llm(provider=provider, model=model, temperature=temperature, api_key=api_key)
    
    graph = StateGraph(AgentState)
    
    # Define Nodes
    graph.add_node("agent", create_agent_node(llm))
    graph.add_node("tools", tools_node)
    
    # Define Edges
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    graph.add_edge("tools", "agent")
    
    # Compile with MemorySaver checkpointer for stateful conversation tracking
    compiled_app = graph.compile(checkpointer=checkpointer if use_memory else None)
    return compiled_app
