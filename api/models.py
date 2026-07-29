from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ScanRequest(BaseModel):
    domain: str
    tools: Optional[List[str]] = None
    threads: Optional[int] = 10
    retries: Optional[int] = 3
    timeout: Optional[int] = 30
    rate_limit: Optional[int] = 100
    format: Optional[str] = "json"
    options: Optional[Dict[str, Any]] = None


class ScanCreateResponse(BaseModel):
    scan_id: str
    domain: str
    status: str
    message: str


class ScanStatusResponse(BaseModel):
    scan_id: str
    domain: str
    status: str
    progress: int
    total_tools: int
    completed_tools: int
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str
    engine: str
