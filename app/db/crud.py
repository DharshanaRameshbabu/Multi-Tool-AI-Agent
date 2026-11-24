from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Task, ToolAuditLog

def create_task(db: Session, title: str, description: Optional[str] = None, priority: str = "Medium", due_date: Optional[str] = None) -> Task:
    task = Task(
        title=title.strip(),
        description=description.strip() if description else None,
        priority=priority.capitalize() if priority else "Medium",
        status="Pending",
        due_date=due_date.strip() if due_date else None
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_tasks(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Task]:
    query = db.query(Task)
    if status:
        query = query.filter(Task.status.ilike(status))
    if priority:
        query = query.filter(Task.priority.ilike(priority))
    return query.order_by(Task.id.desc()).offset(skip).limit(limit).all()

def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()

def update_task(
    db: Session,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    due_date: Optional[str] = None
) -> Optional[Task]:
    task = get_task_by_id(db, task_id)
    if not task:
        return None
    if title is not None:
        task.title = title.strip()
    if description is not None:
        task.description = description.strip()
    if priority is not None:
        task.priority = priority.capitalize()
    if status is not None:
        task.status = status.capitalize()
    if due_date is not None:
        task.due_date = due_date.strip()
    
    db.commit()
    db.refresh(task)
    return task

def complete_task(db: Session, task_id: int) -> Optional[Task]:
    return update_task(db, task_id, status="Completed")

def delete_task(db: Session, task_id: int) -> bool:
    task = get_task_by_id(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True

def log_tool_execution(
    db: Session,
    tool_name: str,
    tool_input: str,
    tool_output: str,
    status: str = "Success",
    execution_time_ms: Optional[float] = None,
    session_id: Optional[str] = None
) -> ToolAuditLog:
    log = ToolAuditLog(
        tool_name=tool_name,
        tool_input=str(tool_input),
        tool_output=str(tool_output),
        status=status,
        execution_time_ms=execution_time_ms,
        session_id=session_id
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_recent_audit_logs(db: Session, limit: int = 50) -> List[ToolAuditLog]:
    return db.query(ToolAuditLog).order_by(ToolAuditLog.id.desc()).limit(limit).all()
