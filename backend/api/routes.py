# backend/api/routes.py

import sys
import os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))

import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.core.chains import chat
from backend.memory.session import get_history, clear_history
from backend.db.redis_client import get_redis_client
from config import settings
# add Supabase check to health_check():
from backend.db.supabase_client import get_supabase_client

app = FastAPI(
    title="Nepal Constitution Legal Chatbot",
    version="2.0.0"
)

redis_client = get_redis_client()

# ── Request/Response Models ───────────────────

class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None  # optional!

class ChatResponse(BaseModel):
    answer: str
    sources: list
    cache_hit: bool
    session_id: str

class HistoryResponse(BaseModel):
    session_id: str
    messages: list
    count: int

class HealthResponse(BaseModel):
    status: str
    version: str
    databases: dict

# ── Endpoints ────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    # check all connections
    # return status of each database
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except Exception:
        redis_status = "disconnected"
    
    return {
        "status": "ok",
        "version": settings.app_version if hasattr(settings, "app_version") else "2.0.0",
        "databases": {
            "redis": redis_status
        }
    }

@app.post("/session", response_model=dict)
def create_session():
    # generate new session_id
    # hint: str(uuid.uuid4())
    # return {"session_id": session_id}
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    # step 1: get or create session_id
    # step 2: call chains.chat()
    # step 3: return response
    session_id = request.session_id or str(uuid.uuid4())

    result = chat(
        question=request.question,
        session_id=session_id
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "cache_hit": result["cache_hit"],
        "session_id": result["session_id"]
    }

@app.get("/history/{session_id}",
         response_model=HistoryResponse)
def get_chat_history(session_id: str):
    # get history from Redis
    # return HistoryResponse
    history = get_history(session_id)

    return {
        "session_id": session_id,
        "messages": history,
        "count": len(history)
    }


@app.delete("/history/{session_id}")
def clear_chat_history(session_id: str):
    # clear history from Redis
    # return success message
    clear_history(session_id)

    return {
        "status": "success",
        "message": f"History cleared for session {session_id}"
    }

@app.get("/cache/stats")
def cache_stats():
    # get all cache keys
    # return count and keys preview
    keys = redis_client.keys("cache:*")

    return {
        "cache_count": len(keys),
        "sample_keys": keys[:10]
    }

@app.get("/health")
def health_check():
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except Exception:
        redis_status = "disconnected"
    
    try:
        supabase = get_supabase_client()
        supabase.table("documents").select("id").limit(1).execute()
        supabase_status = "connected"
    except Exception:
        supabase_status = "disconnected"
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "databases": {
            "redis": redis_status,
            "supabase": supabase_status  # ← add this!
        }
    }