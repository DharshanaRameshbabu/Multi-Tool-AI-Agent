from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.tools.calculator import calculate
from app.tools.search import web_search
from app.tools.task_tool import add_task, list_tasks, complete_task, delete_task
from app.schemas.tool_models import (
    CalculatorInput,
    SearchInput,
    AddTaskInput,
    ListTasksInput,
    CompleteTaskInput,
    DeleteTaskInput
)

@tool("calculator", args_schema=CalculatorInput)
def calculator_tool(expression: str) -> str:
    """
    Perform mathematical operations and calculations safely.
    Use this for:
    - Arithmetic (addition, subtraction, multiplication, division)
    - Percentages (e.g. '25% of 800', '15% of 2500')
    - Exponents, square roots (e.g. 'sqrt(144)', '2^8')
    - Evaluating formulas with precision.
    """
    return calculate(expression)


@tool("web_search", args_schema=SearchInput)
def search_tool(query: str, max_results: int = 4) -> str:
    """
    Search the live web or knowledge base for information.
    Use this for:
    - Finding recent facts, definitions, or overviews
    - Researching topics like 'Retrieval-Augmented Generation' or 'latest developments in AI agents'
    - External information not available in conversation history.
    """
    return web_search(query, max_results=max_results)


@tool("add_task", args_schema=AddTaskInput)
def add_task_tool(
    title: str,
    description: Optional[str] = None,
    priority: Optional[str] = "Medium",
    due_date: Optional[str] = None
) -> str:
    """
    Add a new task or to-do item to the task management database.
    Use this whenever the user asks to save, record, or add a task, reminder, or goal.
    """
    return add_task(title=title, description=description, priority=priority or "Medium", due_date=due_date)


@tool("list_tasks", args_schema=ListTasksInput)
def list_tasks_tool(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Retrieve and list saved tasks from the database.
    Use this when the user asks:
    - 'What tasks have I saved?'
    - 'Show my pending tasks'
    - 'List high priority tasks'
    """
    return list_tasks(status=status, priority=priority, limit=limit)


@tool("complete_task", args_schema=CompleteTaskInput)
def complete_task_tool(task_id: int) -> str:
    """
    Mark an existing task as completed in the database using its ID.
    Use this when the user asks to finish, complete, or check off a task.
    """
    return complete_task(task_id=task_id)


@tool("delete_task", args_schema=DeleteTaskInput)
def delete_task_tool(task_id: int, confirm: bool = True) -> str:
    """
    Delete a task from the database by ID.
    Requires confirm=True to prevent accidental data loss.
    """
    return delete_task(task_id=task_id, confirm=confirm)


# List of all available tools
ALL_TOOLS = [
    calculator_tool,
    search_tool,
    add_task_tool,
    list_tasks_tool,
    complete_task_tool,
    delete_task_tool,
]

# Map tool name -> callable
TOOL_MAP = {t.name: t for t in ALL_TOOLS}

def get_tools_metadata() -> List[Dict[str, Any]]:
    """Return documentation & schema metadata for all tools."""
    metadata = []
    for t in ALL_TOOLS:
        metadata.append({
            "name": t.name,
            "description": t.description,
            "args": t.args if hasattr(t, "args") else {},
        })
    return metadata
