from fastapi import APIRouter, HTTPException, Depends
from langchain_core.messages import HumanMessage
from app.schemas.chat import ChatRequest, ChatResponse, ToolExecutionStep
from app.agent.workflow import build_agent_graph
from app.core.logging import logger

router = APIRouter(prefix="/api/chat", tags=["Chat & Agent"])

@router.post("", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Send a natural language instruction or query to the Multi-Tool AI Agent.
    The agent dynamically decides whether to invoke tools (Calculator, Search, Tasks)
    or respond directly, retaining session memory.
    """
    try:
        session_id = request.session_id or "default_session"
        agent_graph = build_agent_graph(
            provider=request.provider,
            model=request.model,
            temperature=request.temperature
        )

        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "session_id": session_id,
            "tool_calls_trace": [],
            "iteration_count": 0,
            "error": None
        }

        # Session-aware thread configuration for LangGraph checkpointing
        config = {"configurable": {"thread_id": session_id}}

        # Execute workflow
        result = agent_graph.invoke(inputs, config=config)

        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, "content") else str(last_message)
        
        # Collect tool execution trace
        trace_data = [
            ToolExecutionStep(
                tool_name=t["tool_name"],
                tool_input=t["tool_input"],
                tool_output=t["tool_output"],
                status=t.get("status", "success"),
                execution_time_ms=t.get("execution_time_ms")
            )
            for t in result.get("tool_calls_trace", [])
        ]

        model_name = request.model or request.provider or "default-agent"

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            tool_calls=trace_data,
            model_used=model_name,
            iteration_count=result.get("iteration_count", 1)
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent workflow error: {str(e)}")
