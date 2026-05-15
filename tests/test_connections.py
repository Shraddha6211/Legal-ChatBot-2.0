import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.db.supabase_client import get_supabase_client
from backend.db.redis_client import get_redis_client, save_to_redis, get_from_redis

def test_supabase():
    print("Testing Supabase...")
    supabase = get_supabase_client()
    
    # test if documents table exists
    result = supabase.table("documents").select("id").limit(1).execute()
    print(f"Documents table accessible: ✅")
    print(f"Current rows: {len(result.data)}")
    print("Supabase ✅")

def test_redis():
    print("\nTesting Redis...")
    client = get_redis_client()
    save_to_redis(client, "test:key", {"message": "hello!"}, ttl=60)
    result = get_from_redis(client, "test:key")
    print(f"Redis result: {result}")
    print("Redis ✅")

if __name__ == "__main__":
    test_supabase()
    test_redis()