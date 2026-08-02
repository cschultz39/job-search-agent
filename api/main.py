# --------------------------------
#            imports
# --------------------------------
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel

import sys
import os

# allows main to access sheet_tools while living folder below repo root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sheet_tools import get_status_counts, search_jobs, mark_status, get_status_history_weekly
from agent import ask_agent

app = FastAPI(title="Job Search Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
#           endpoints
# --------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/metrics")
def get_metrics():
    return get_status_counts()

@app.get("/jobs")
def get_jobs(status: Optional[str] = None, min_score: Optional[int] = None, company: Optional[str] = None, limit: int = 10):
    return search_jobs(status=status, min_score=min_score, company=company, limit=limit)

class StatusUpdate(BaseModel):
    job_id: str
    new_status: str
@app.patch("/jobs/status")
def update_job_status(update: StatusUpdate):
    result = mark_status(update.job_id, update.new_status)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/history")
def get_history():
    return get_status_history_weekly()

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []
@app.post("/chat")
def chat(request: ChatRequest):
    return ask_agent(request.message, request.conversation_history)

