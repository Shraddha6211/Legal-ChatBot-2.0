from backend.db.pinecone_client import get_pinecone_index
from backend.db.redis_client import get_redis_client, save_to_redis, get_from_redis

def test_pinecone():
    print("Testing Pinecone...")
    index = get_pinecone_index()
    print(f"Pinecone index: {index}")
    print("Pinecone ✅")

def test_redis():
    print("Testing Redis...")
    client = get_redis_client()
    
    # test save and get
    save_to_redis(client, "test:key", {"message": "hello!"}, ttl=60)
    result = get_from_redis(client, "test:key")
    print(f"Redis result: {result}")
    
    # test missing key
    missing = get_from_redis(client, "nonexistent:key")
    print(f"Missing key returns: {missing}")
    print("Redis ✅")

if __name__ == "__main__":
    test_pinecone()
    test_redis()