from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ToolExecutionStep(BaseModel):
    tool_name: str
    tool_input: Any
    tool_output: str
    status: str = "success"  # success, error
    execution_time_ms: Optional[float] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's query or instruction")
    session_id: Optional[str] = Field("default_session", description="Conversation session ID for conversational memory")
    provider: Optional[str] = Field(None, description="LLM provider: groq, openai, google, mock")
    model: Optional[str] = Field(None, description="Model identifier override")
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Sampling temperature")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent final answer")
    session_id: str = Field(..., description="Active session ID")
    tool_calls: List[ToolExecutionStep] = Field(default_factory=list, description="Trace of all tools executed during this turn")
    model_used: str = Field(..., description="Model and provider that handled the request")
    iteration_count: int = Field(default=1, description="Number of agent reasoning loops")

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[str]
    tool_name: str
    tool_input: str
    tool_output: str
    status: str
    execution_time_ms: Optional[float]
    timestamp: Optional[datetime]
