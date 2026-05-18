# backend/memory/cache.py

import sys
import os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))

import hashlib
import numpy as np
from backend.db.redis_client import (
    get_redis_client,
    save_to_redis,
    get_from_redis
)
from config import settings

redis_client = get_redis_client()

CACHE_SIMILARITY_THRESHOLD = 0.75


def get_cache_key(question: str) -> str:
    # hash question to create Redis key
    # hint: hashlib.md5(question.encode()).hexdigest()
    # format: "cache:{hash}"
    key = hashlib.md5(question.encode()).hexdigest()
    return f"cache:{key}"


def cosine_similarity(vec1: list, vec2: list) -> float:
    # compute similarity between two vectors
    # hint: use numpy!
    # np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def save_to_cache(
    question: str,
    answer: str,
    question_embedding: list
) -> None:
    # step 1: get cache key
    key = get_cache_key(question)
    # step 2: build cache entry dict
    entry = {
        "question": question,
        "answer": answer,
        "question_embedding": question_embedding
        
    }
    # step 3: save to Redis with TTL
    save_to_redis(redis_client, key, entry, ttl=settings.cache_ttl_seconds)



def search_cache(
    question: str,
    question_embedding: list
) -> str | None:
    """
    Search cache for similar question.
    Returns cached answer or None.
    """
    # step 1: get all cache keys
    # hint: redis_client.keys("cache:*")
    keys= redis_client.keys("cache:*")
    
    # step 2: for each cached entry:
    #   → get the entry
    #   → compute similarity with question_embedding
    #   → if similarity > threshold → return answer!
    
    # step 3: return None if no match found
    if not keys:
        print("Cache empty!")
        return None
    
    print(f"Searching {len(keys)} cached entries...")

    best_similarity = 0
    best_answer = None

    for key in keys:
        entry = get_from_redis(redis_client, key)
        if not entry:
            continue
        
        similarity = cosine_similarity(
            question_embedding,
            entry['question_embedding']
        )
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_answer = entry['answer']
           
    if best_similarity > CACHE_SIMILARITY_THRESHOLD:
        print(f"Cache HIT! similarity: {best_similarity:.3f}")
        return best_answer
    
    print(f"Cache MISS! best similarity: {best_similarity:.3f}")
    return None