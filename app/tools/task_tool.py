from typing import Optional
from app.db.database import SessionLocal, init_db
from app.db import crud
from app.core.logging import logger
from app.core.config import settings

# Initialize DB tables on import
init_db()

def add_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "Medium",
    due_date: Optional[str] = None
) -> str:
    """
    Add a new task to the task management database.
    
    Parameters:
    - title: Brief summary or name of the task (e.g. 'Learn LangGraph')
    - description: Optional additional details or instructions
    - priority: Priority level ('Low', 'Medium', 'High')
    - due_date: Optional due date or timeline (e.g. 'Tomorrow', 'Friday', '2026-11-25')
    """
    if not title or not title.strip():
        return "Error: Task title cannot be empty."

    db = SessionLocal()
    try:
        task = crud.create_task(
            db=db,
            title=title.strip(),
            description=description,
            priority=priority,
            due_date=due_date
        )
        logger.info(f"Task added: ID={task.id}, Title='{task.title}'")
        msg = f"Successfully added task #{task.id}: '{task.title}'"
        if task.priority:
            msg += f" [Priority: {task.priority}]"
        if task.due_date:
            msg += f" [Due: {task.due_date}]"
        return msg
    except Exception as e:
        logger.error(f"Failed to add task: {e}")
        return f"Error adding task: {str(e)}"
    finally:
        db.close()


def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Retrieve saved tasks from the database.
    
    Parameters:
    - status: Optional filter by status ('Pending' or 'Completed')
    - priority: Optional filter by priority ('Low', 'Medium', 'High')
    - limit: Maximum number of tasks to retrieve (default 20)
    """
    db = SessionLocal()
    try:
        tasks = crud.get_tasks(db=db, status=status, priority=priority, limit=limit)
        if not tasks:
            filter_desc = []
            if status:
                filter_desc.append(f"status='{status}'")
            if priority:
                filter_desc.append(f"priority='{priority}'")
            filter_str = f" with {', '.join(filter_desc)}" if filter_desc else ""
            return f"No tasks found{filter_str}."

        lines = [f"Found {len(tasks)} task(s):"]
        for t in tasks:
            status_icon = "[X]" if t.status.lower() == "completed" else "[ ]"
            due_str = f" | Due: {t.due_date}" if t.due_date else ""
            desc_str = f" - {t.description}" if t.description else ""
            lines.append(f"#{t.id} {status_icon} [{t.status}] {t.title} (Priority: {t.priority}{due_str}){desc_str}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return f"Error retrieving tasks: {str(e)}"
    finally:
        db.close()


def complete_task(task_id: int) -> str:
    """
    Mark an existing task as completed in the database.
    
    Parameters:
    - task_id: The unique integer ID of the task
    """
    db = SessionLocal()
    try:
        task = crud.complete_task(db=db, task_id=task_id)
        if not task:
            return f"Error: Task with ID #{task_id} not found."
        logger.info(f"Task #{task_id} marked as completed")
        return f"Task #{task_id} ('{task.title}') has been marked as completed."
    except Exception as e:
        logger.error(f"Failed to complete task #{task_id}: {e}")
        return f"Error updating task: {str(e)}"
    finally:
        db.close()


def delete_task(task_id: int, confirm: bool = True) -> str:
    """
    Delete a task from the database.
    
    Parameters:
    - task_id: The unique integer ID of the task to delete
    - confirm: Must be True to execute deletion (Safety Guardrail)
    """
    if not confirm:
        return (
            f"Deletion cancelled: Safety confirmation was not provided. "
            f"To delete task #{task_id}, explicit confirmation (confirm=True) is required."
        )

    db = SessionLocal()
    try:
        task = crud.get_task_by_id(db=db, task_id=task_id)
        if not task:
            return f"Error: Task with ID #{task_id} not found."
        title = task.title
        success = crud.delete_task(db=db, task_id=task_id)
        if success:
            logger.info(f"Task #{task_id} deleted")
            return f"Task #{task_id} ('{title}') was successfully deleted."
        return f"Error: Could not delete task #{task_id}."
    except Exception as e:
        logger.error(f"Failed to delete task #{task_id}: {e}")
        return f"Error deleting task: {str(e)}"
    finally:
        db.close()
