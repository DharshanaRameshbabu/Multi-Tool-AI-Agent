import os
import re
import uuid
from typing import Any, List, Optional, Sequence
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from app.core.config import settings
from app.core.logging import logger

class MockToolCallingLLM(BaseChatModel):
    """
    Deterministic rule-based LLM emulator for testing and offline environments.
    Inspects user queries and properly generates tool calls or final synthesized responses.
    """
    model_name: str = "mock-agent-v1"
    bound_tools: List[Any] = []

    @property
    def _llm_type(self) -> str:
        return "mock-tool-calling-llm"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "MockToolCallingLLM":
        self.bound_tools = list(tools)
        return self

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        last_msg = messages[-1] if messages else HumanMessage(content="")
        
        # If the last message is a ToolMessage, synthesize the final response based on tool results
        if isinstance(last_msg, ToolMessage):
            tool_output = last_msg.content
            tool_name = getattr(last_msg, "name", "tool")
            
            # Find the original user query
            user_query = ""
            for m in reversed(messages):
                if isinstance(m, HumanMessage):
                    user_query = m.content
                    break
                    
            if tool_name == "calculator":
                reply = f"Based on the calculation, the result is: {tool_output}."
            elif tool_name == "web_search":
                reply = f"Here is the information I retrieved regarding your search:\n\n{tool_output}"
            elif "task" in tool_name:
                reply = f"Here is the update from your task manager:\n{tool_output}"
            else:
                reply = f"Tool execution result: {tool_output}"
                
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply))])

        # If user message, decide if tool calling is required
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        content_lower = content.lower().strip()

        # 1. Calculator Trigger
        calc_match = re.search(r'(?:calculate|what is|compute|\bof\b|\+|\-|\*|\/|\%|\^|sqrt)\s*([0-9\.\,\%\s\+\-\*\/\^\(\)]+)', content, re.IGNORECASE)
        math_keywords = ["%", "plus", "minus", "times", "multiplied by", "divided by", "sqrt", "calculate", "25%", "15%"]
        is_math = any(kw in content_lower for kw in math_keywords) or (calc_match and any(char.isdigit() for char in content))

        if is_math and any(char.isdigit() for char in content):
            # Extract expression
            expr = content
            for prefix in ["calculate", "what is", "compute", "evaluate", "please"]:
                expr = re.sub(rf"^{prefix}\s+", "", expr, flags=re.IGNORECASE)
            expr = expr.strip(" ?.")
            
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            tool_call = {
                "name": "calculator",
                "args": {"expression": expr},
                "id": call_id,
            }
            ai_msg = AIMessage(
                content="",
                tool_calls=[tool_call]
            )
            return ChatResult(generations=[ChatGeneration(message=ai_msg)])

        # 2. Add Task Trigger
        add_task_match = re.search(r'(?:add|create|save|record|schedule)\s+(?:a\s+)?task\s+(?:to|called|named|for)?\s*["\']?([^"\']+)["\']?', content, re.IGNORECASE)
        if add_task_match or ("task" in content_lower and ("add" in content_lower or "create" in content_lower or "schedule" in content_lower)):
            task_title = "New Task"
            if add_task_match:
                task_title = add_task_match.group(1).strip()
            else:
                task_title = content.replace("add task", "").replace("create task", "").strip(" :.-")

            # Check for due date
            due_date = None
            if "tomorrow" in content_lower:
                due_date = "Tomorrow"
                task_title = re.sub(r'\btomorrow\b', '', task_title, flags=re.IGNORECASE).strip()
            elif "today" in content_lower:
                due_date = "Today"
                task_title = re.sub(r'\btoday\b', '', task_title, flags=re.IGNORECASE).strip()
                
            priority = "High" if "high" in content_lower else ("Low" if "low" in content_lower else "Medium")
            
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            tool_call = {
                "name": "add_task",
                "args": {
                    "title": task_title or "Untitled Task",
                    "priority": priority,
                    "due_date": due_date
                },
                "id": call_id,
            }
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[tool_call]))])

        # 3. List Tasks Trigger
        if any(phrase in content_lower for phrase in ["retrieve my tasks", "what tasks", "list tasks", "show tasks", "get tasks", "saved tasks", "my tasks"]):
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            tool_call = {
                "name": "list_tasks",
                "args": {},
                "id": call_id,
            }
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[tool_call]))])

        # 4. Search Trigger
        if any(phrase in content_lower for phrase in ["search", "find information", "lookup", "who is", "explain the latest", "retrieval-augmented generation", "latest developments"]):
            search_query = content
            for prefix in ["search for", "find information about", "find information on", "lookup", "explain the latest developments in"]:
                search_query = re.sub(rf"^{prefix}\s*", "", search_query, flags=re.IGNORECASE)
            search_query = search_query.strip(" ?.")
            
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            tool_call = {
                "name": "web_search",
                "args": {"query": search_query or content},
                "id": call_id,
            }
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[tool_call]))])

        # Default: General conversational answer without tool use
        direct_reply = (
            f"Hello! I am your Intelligent Task Assistant. I can perform calculations, "
            f"search the web, and manage your tasks in SQLite. How may I assist you today?"
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=direct_reply))])


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    api_key: Optional[str] = None
) -> BaseChatModel:
    """
    Factory function to instantiate and configure LLM instances based on provider and settings.
    Gracefully falls back to MockToolCallingLLM if no API key is supplied.
    """
    chosen_provider = (provider or settings.LLM_PROVIDER).lower()
    
    # 1. Groq Provider
    if chosen_provider == "groq":
        key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        if key and not key.startswith("your_"):
            try:
                from langchain_groq import ChatGroq
                model_name = model or settings.DEFAULT_MODEL or "llama-3.3-70b-versatile"
                logger.info(f"Initialized Groq LLM: {model_name}")
                return ChatGroq(model=model_name, api_key=key, temperature=temperature)
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGroq: {e}. Falling back to mock model.")
        else:
            logger.info("No Groq API key found. Operating in local Mock/Rule-based mode.")

    # 2. OpenAI Provider
    elif chosen_provider == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if key and not key.startswith("your_"):
            try:
                from langchain_openai import ChatOpenAI
                model_name = model or "gpt-4o-mini"
                logger.info(f"Initialized OpenAI LLM: {model_name}")
                return ChatOpenAI(model=model_name, api_key=key, temperature=temperature)
            except Exception as e:
                logger.warning(f"Failed to initialize ChatOpenAI: {e}. Falling back to mock model.")
        else:
            logger.info("No OpenAI API key found. Operating in local Mock/Rule-based mode.")

    # 3. Google Gemini Provider
    elif chosen_provider in ["google", "gemini"]:
        key = api_key or os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
        if key and not key.startswith("your_"):
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                model_name = model or "gemini-1.5-flash"
                logger.info(f"Initialized Google Gemini LLM: {model_name}")
                return ChatGoogleGenerativeAI(model=model_name, google_api_key=key, temperature=temperature)
            except Exception as e:
                logger.warning(f"Failed to initialize ChatGoogleGenerativeAI: {e}. Falling back to mock model.")
        else:
            logger.info("No Google API key found. Operating in local Mock/Rule-based mode.")

    # 4. Fallback Mock Model
    logger.info("Using MockToolCallingLLM (deterministic, offline-ready).")
    return MockToolCallingLLM()
