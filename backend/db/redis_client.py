# backend/db/redis_client.py

import redis
import json
from config import settings

def get_redis_client():
    # step 1: create redis client from URL
    # hint: redis.from_url(settings.redis_url)
    client = redis.from_url(settings.redis_url, decode_responses= True)
    
    # step 2: test connection
    # hint: client.ping() returns True if connected
    try:
        client.ping()
        print("Connected to Redis successfully.")
    except redis.ConnectionError:
        print("Failed to connect to Redis")
        raise
    # step 3: return client
    return client

def save_to_redis(client, key, value, ttl=None):
    # value might be dict → need to convert to string
    # hint: json.dumps(value)
    # hint: client.set(key, value)
    # hint: if ttl: client.expire(key, ttl)
    json_string = json.dumps(value)
    client.set(key, json_string)
    if ttl: 
        client.expire(key, ttl)
    print(f"Saved to Redis: {key}")

def get_from_redis(client, key):
    # get value, convert back to dict
    # hint: client.get(key) → returns None if not found!
    value = client.get(key) 
    if value is None:
        return None
    return json.loads(value)
    # hint: json.loads(value) converts string → dict
    