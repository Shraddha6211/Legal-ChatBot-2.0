import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.memory.session import (
    get_history, save_message, clear_history
)
from backend.memory.cache import save_to_cache, search_cache
from langchain_openai import OpenAIEmbeddings
from config import settings

embeddings_model = OpenAIEmbeddings(
    model=settings.embedding_model,
    openai_api_key=settings.openai_api_key
)

def test_session_memory():
    print("=== Testing Session Memory ===")
    session_id = "test-session-123"
    
    # clear first
    clear_history(session_id)
    
    # save messages
    save_message(session_id, "user", "What is Article 18?")
    save_message(session_id, "assistant", "Article 18 guarantees equality...")
    save_message(session_id, "user", "Tell me more")
    
    # retrieve
    history = get_history(session_id)
    print(f"Messages saved: {len(history)}")
    for msg in history:
        print(f"  {msg['role']}: {msg['content'][:50]}")
    
    print("Session Memory ✅\n")

def test_semantic_cache():
    print("=== Testing Semantic Cache ===")
    
    question = "What is the right to equality?"
    answer = "Article 18 guarantees equality before law..."
    
    # embed question
    embedding = embeddings_model.embed_query(question)
    
    # save to cache
    save_to_cache(question, answer, embedding)
    
    # search with SAME question
    result = search_cache(question, embedding)
    print(f"Exact match: {result[:50] if result else 'None'}")
    
    # search with SIMILAR question
    similar = "Tell me about right to equality in Nepal"
    similar_embedding = embeddings_model.embed_query(similar)
    result2 = search_cache(similar, similar_embedding)
    print(f"Similar match: {result2[:50] if result2 else 'None'}")
    
    # search with DIFFERENT question
    different = "How is the President elected?"
    diff_embedding = embeddings_model.embed_query(different)
    result3 = search_cache(different, diff_embedding)
    print(f"Different match: {result3 if result3 else 'None (correct!)'}")
    
    print("Semantic Cache ✅")

if __name__ == "__main__":
    test_session_memory()
    test_semantic_cache()