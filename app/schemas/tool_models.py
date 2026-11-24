from typing import Optional
from pydantic import BaseModel, Field

class CalculatorInput(BaseModel):
    expression: str = Field(
        ...,
        description="Mathematical expression to calculate, e.g., '25% of 800', '120 * 45', '(15 / 100) * 2500', 'sqrt(144) + 12'"
    )

class SearchInput(BaseModel):
    query: str = Field(
        ...,
        description="Search term or topic to look up on the web, e.g., 'Retrieval-Augmented Generation', 'latest developments in AI agents'"
    )
    max_results: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of search results to retrieve"
    )

class AddTaskInput(BaseModel):
    title: str = Field(..., description="Title of the task to add, e.g., 'Learn LangGraph'")
    description: Optional[str] = Field(None, description="Detailed description or notes about the task")
    priority: Optional[str] = Field("Medium", description="Priority level: 'Low', 'Medium', or 'High'")
    due_date: Optional[str] = Field(None, description="Optional due date or time, e.g., 'Tomorrow', 'Friday'")

class ListTasksInput(BaseModel):
    status: Optional[str] = Field(None, description="Filter by status: 'Pending', 'Completed', or leave empty for all")
    priority: Optional[str] = Field(None, description="Filter by priority: 'Low', 'Medium', 'High', or leave empty")
    limit: int = Field(default=20, ge=1, le=100, description="Max number of tasks to return")

class CompleteTaskInput(BaseModel):
    task_id: int = Field(..., description="The integer ID of the task to mark as completed")

class DeleteTaskInput(BaseModel):
    task_id: int = Field(..., description="The integer ID of the task to delete")
    confirm: bool = Field(
        default=True,
        description="Confirmation flag to prevent accidental deletion"
    )
