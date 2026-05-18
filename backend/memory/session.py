# backend/memory/session.py

import sys
import os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))

from backend.db.redis_client import (
    get_redis_client,
    save_to_redis,
    get_from_redis
)
from config import settings

# module level redis connection
redis_client = get_redis_client()


def get_session_key(session_id: str) -> str:
    # return Redis key for this session
    # format: "session:{session_id}:history"
    # get_session_key:
    return f"session:{session_id}:history"

def get_history(session_id: str) -> list:
    # get conversation history for session
    key = get_session_key(session_id)
    history = get_from_redis(redis_client, key)
    # return empty list if no history!
    return history if history else []
    
def save_message(session_id: str, role: str, content: str) -> None:
    # get existing history
    key = get_session_key(session_id)
    history = get_history(session_id)
    # append new message: {"role": role, "content": content}
    history.append({"role": role, "content": content})
    # keep only last N messages:
    history = history[-settings.max_history_messages:]
    # save back to Redis with TTL
    save_to_redis(redis_client, key, history, ttl=settings.session_ttl_seconds)


def clear_history(session_id: str) -> None:
    key = get_session_key(session_id)
    redis_client.delete(key)