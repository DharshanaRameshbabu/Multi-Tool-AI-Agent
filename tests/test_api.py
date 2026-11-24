import pytest
import sys
from pathlib import Path
from starlette.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Multi-Tool AI Agent" in data["project"]

def test_get_tools_endpoint():
    response = client.get("/api/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) >= 5
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "web_search" in names
    assert "add_task" in names

def test_tasks_crud_api():
    # 1. Create Task
    task_payload = {
        "title": "API Test Task",
        "description": "Created via automated test",
        "priority": "High",
        "due_date": "Tomorrow"
    }
    res_create = client.post("/api/tasks", json=task_payload)
    assert res_create.status_code == 201
    created = res_create.json()
    task_id = created["id"]
    assert created["title"] == "API Test Task"
    assert created["priority"] == "High"

    # 2. Get Single Task
    res_get = client.get(f"/api/tasks/{task_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == task_id

    # 3. Complete Task
    res_comp = client.post(f"/api/tasks/{task_id}/complete")
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "Completed"

    # 4. Delete Task without confirm -> 400 Bad Request
    res_del_fail = client.delete(f"/api/tasks/{task_id}?confirm=false")
    assert res_del_fail.status_code == 400

    # 5. Delete Task with confirm=true -> 200 OK
    res_del_ok = client.delete(f"/api/tasks/{task_id}?confirm=true")
    assert res_del_ok.status_code == 200

def test_chat_api_calculator():
    chat_payload = {
        "message": "Calculate 25% of 800",
        "session_id": "test_api_session"
    }
    response = client.post("/api/chat", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert "200" in data["response"]
    assert len(data["tool_calls"]) > 0
    assert data["tool_calls"][0]["tool_name"] == "calculator"
