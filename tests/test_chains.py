import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.core.chains import chat

def test_chat():
    session_id = "test-session-456"
    
    # test 1: knowledge base query
    print("=== Test 1: Knowledge Base ===")
    result = chat("What is the right to equality?", session_id)
    print(f"Cache hit: {result['cache_hit']}")
    print(f"Sources: {len(result['sources'])}")
    print(f"Answer: {result['answer'][:150]}")
    print()
    
    # test 2: same question → should hit cache!
    print("=== Test 2: Cache Hit ===")
    result2 = chat("What is the right to equality?", session_id)
    print(f"Cache hit: {result2['cache_hit']}")
    print()
    
    # test 3: follow-up → should use memory!
    print("=== Test 3: Memory ===")
    result3 = chat("Tell me more about that", session_id)
    print(f"Cache hit: {result3['cache_hit']}")
    print(f"Answer: {result3['answer'][:150]}")
    print()
    
    # test 4: specific article
    print("=== Test 4: Specific Article ===")
    result4 = chat("What does Article 18 say?", session_id)
    print(f"Answer: {result4['answer'][:150]}")

if __name__ == "__main__":
    test_chat()