from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["Task Management"])

@router.get("", response_model=List[TaskResponse])
def get_all_tasks(
    status: Optional[str] = Query(None, description="Filter by status: 'Pending' or 'Completed'"),
    priority: Optional[str] = Query(None, description="Filter by priority: 'Low', 'Medium', 'High'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all tasks with optional filtering by status or priority."""
    tasks = crud.get_tasks(db, status=status, priority=priority, skip=skip, limit=limit)
    return tasks

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    task = crud.create_task(
        db=db,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority.value if task_in.priority else "Medium",
        due_date=task_in.due_date
    )
    return task

@router.get("/{task_id}", response_model=TaskResponse)
def get_single_task(task_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific task by its unique ID."""
    task = crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_existing_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    """Update an existing task's properties."""
    task = crud.update_task(
        db=db,
        task_id=task_id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority.value if task_in.priority else None,
        status=task_in.status.value if task_in.status else None,
        due_date=task_in.due_date
    )
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return task

@router.post("/{task_id}/complete", response_model=TaskResponse)
def mark_task_as_completed(task_id: int, db: Session = Depends(get_db)):
    """Mark a task as completed."""
    task = crud.complete_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return task

@router.delete("/{task_id}")
def delete_existing_task(
    task_id: int,
    confirm: bool = Query(True, description="Safety flag to confirm permanent deletion"),
    db: Session = Depends(get_db)
):
    """Delete a task from the database. Requires confirm=True."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Safety Guardrail: Deletion cancelled. You must supply confirm=true."
        )
    success = crud.delete_task(db=db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return {"message": f"Task #{task_id} successfully deleted", "id": task_id}
