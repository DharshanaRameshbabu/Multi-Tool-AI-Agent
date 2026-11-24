from typing import Annotated, Sequence, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Represents the internal state of the Multi-Tool AI Agent in LangGraph.
    - messages: Sequence of chat messages (SystemMessage, HumanMessage, AIMessage, ToolMessage)
    - session_id: Unique identifier for conversation continuity
    - tool_calls_trace: Detailed logs of tool invocations for UI inspection & audit logging
    - iteration_count: Safety guard to prevent runaway recursion loops
    - error: Optional error message if a critical failure occurs
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    session_id: str
    tool_calls_trace: List[Dict[str, Any]]
    iteration_count: int
    error: Optional[str]
