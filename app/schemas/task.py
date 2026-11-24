from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class PriorityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class StatusEnum(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Brief title of the task")
    description: Optional[str] = Field(None, max_length=1000, description="Optional detailed description")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, description="Task priority (Low, Medium, High)")
    due_date: Optional[str] = Field(None, max_length=100, description="Optional due date (e.g., 'Tomorrow', '2026-11-25')")

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v_cap = v.capitalize()
            if v_cap in [p.value for p in PriorityEnum]:
                return v_cap
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    due_date: Optional[str] = None

class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusEnum
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
