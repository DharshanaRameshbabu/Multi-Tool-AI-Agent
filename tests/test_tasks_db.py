import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db.database import SessionLocal, init_db
from app.db import crud
from app.tools.task_tool import add_task, list_tasks, complete_task, delete_task

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_add_and_list_tasks():
    # Test adding tasks
    res_add = add_task("Learn LangGraph", description="Agent workflows", priority="High", due_date="Tomorrow")
    assert "Successfully added task" in res_add
    assert "Learn LangGraph" in res_add
    
    # Test listing
    res_list = list_tasks()
    assert "Learn LangGraph" in res_list

def test_complete_task():
    db = SessionLocal()
    task = crud.create_task(db, title="Test Complete", priority="Medium")
    task_id = task.id
    db.close()

    res_comp = complete_task(task_id)
    assert f"Task #{task_id}" in res_comp
    assert "marked as completed" in res_comp

def test_delete_task_with_safety_guardrail():
    db = SessionLocal()
    task = crud.create_task(db, title="Task to Delete", priority="Low")
    task_id = task.id
    db.close()

    # Safety: confirm=False should prevent deletion
    res_abort = delete_task(task_id, confirm=False)
    assert "Deletion cancelled" in res_abort

    # confirm=True executes deletion
    res_success = delete_task(task_id, confirm=True)
    assert "successfully deleted" in res_success

def test_nonexistent_task_operations():
    res_comp = complete_task(999999)
    assert "not found" in res_comp

    res_del = delete_task(999999, confirm=True)
    assert "not found" in res_del
