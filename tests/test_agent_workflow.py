import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent.workflow import build_agent_graph
from langchain_core.messages import HumanMessage

def test_agent_routes_to_calculator():
    agent = build_agent_graph(provider="mock")
    inputs = {
        "messages": [HumanMessage(content="What is 25% of 800?")],
        "session_id": "test_calc_session",
        "tool_calls_trace": [],
        "iteration_count": 0,
        "error": None
    }
    result = agent.invoke(inputs, config={"configurable": {"thread_id": "test_calc_session"}})
    
    # Must use calculator
    tool_names = [t["tool_name"] for t in result.get("tool_calls_trace", [])]
    assert "calculator" in tool_names
    assert "200" in result["messages"][-1].content

def test_agent_routes_to_add_task():
    agent = build_agent_graph(provider="mock")
    inputs = {
        "messages": [HumanMessage(content="Add a task to learn LangGraph tomorrow")],
        "session_id": "test_task_session",
        "tool_calls_trace": [],
        "iteration_count": 0,
        "error": None
    }
    result = agent.invoke(inputs, config={"configurable": {"thread_id": "test_task_session"}})
    
    tool_names = [t["tool_name"] for t in result.get("tool_calls_trace", [])]
    assert "add_task" in tool_names

def test_agent_routes_to_list_tasks():
    agent = build_agent_graph(provider="mock")
    inputs = {
        "messages": [HumanMessage(content="Retrieve my saved tasks")],
        "session_id": "test_list_session",
        "tool_calls_trace": [],
        "iteration_count": 0,
        "error": None
    }
    result = agent.invoke(inputs, config={"configurable": {"thread_id": "test_list_session"}})
    
    tool_names = [t["tool_name"] for t in result.get("tool_calls_trace", [])]
    assert "list_tasks" in tool_names

def test_agent_general_conversation_no_tools():
    agent = build_agent_graph(provider="mock")
    inputs = {
        "messages": [HumanMessage(content="Hello, who are you?")],
        "session_id": "test_general_session",
        "tool_calls_trace": [],
        "iteration_count": 0,
        "error": None
    }
    result = agent.invoke(inputs, config={"configurable": {"thread_id": "test_general_session"}})
    
    # No tools should be called for simple greetings
    assert len(result.get("tool_calls_trace", [])) == 0
    assert len(result["messages"][-1].content) > 0
