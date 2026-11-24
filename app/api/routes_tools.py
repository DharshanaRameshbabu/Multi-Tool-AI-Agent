from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.tools.registry import get_tools_metadata
from app.schemas.chat import AuditLogResponse

router = APIRouter(prefix="/api/tools", tags=["Tools & Audit Logs"])

@router.get("", response_model=List[Dict[str, Any]])
def list_available_tools():
    """Retrieve metadata and parameter definitions for all available agent tools."""
    return get_tools_metadata()

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_tool_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve historical logs of all tool executions."""
    logs = crud.get_recent_audit_logs(db=db, limit=limit)
    return logs
