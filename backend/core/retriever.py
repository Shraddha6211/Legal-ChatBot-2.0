# backend/core/retriever.py

import sys
import os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))))

from langchain_openai import OpenAIEmbeddings
from backend.db.supabase_client import get_supabase_client
from config import settings
from gensim.parsing.preprocessing import remove_stopwords
from openai import OpenAI
from backend.db.supabase_client import get_supabase_client

# ── Module level connections ──────────────────
# (loaded once when file imports!)
supabase = get_supabase_client()

embeddings_model = OpenAIEmbeddings(
    model=settings.embedding_model,
    openai_api_key=settings.openai_api_key
)

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=settings.openai_api_key)

# ── Query Expansion ───────────────────────────

def expand_query(question: str) -> str:
    # step 1: lowercase
    question = question.lower()

    # step 2: remove filler phrases
    stop_phrases = ["what is", "what are", "how is", "tell me about", "explain", "define"]
    for phrase in stop_phrases:
        question = question.replace(phrase, "")

    # step 3: remove leading the/a/an
    question = question.strip()
    for word in ["the ", "a ", "an "]:
        if question.startswith(word):
            question = question[len(word):]
    
    # step 4: return clean question
    return question.strip()

def enrich_query(clean_question: str) -> str:
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": """You are a legal search assistant.
                Given a question about Nepal's Constitution,
                generate 5-8 related legal terms or phrases
                that might appear in the Constitution.
                Return ONLY the terms, comma separated.
                No explanation, no sentences."""
            },
            {
                "role": "user",
                "content": f"Question: {clean_question}"
            }
        ],
        max_tokens=100
    )
    related_terms = response.choices[0].message.content
    return f"{clean_question} {related_terms}"
    
# ── Core Retrieval ────────────────────────────

def search_supabase(
    query_text: str,
    threshold: float = settings.similarity_threshold,
    k: int = settings.top_k_results
) -> list:
    # step 1: embed the query
    # hint: embeddings_model.embed_query(query_text)
    embedding = embeddings_model.embed_query(query_text)

    # step 2: call match_documents via RPC
    # hint: supabase.rpc('match_documents', {
    #     'query_embedding': embedding,
    #     'match_threshold': threshold,
    #     'match_count': k
    # }).execute()
    result = supabase.rpc('match_documents', {
        'query_embedding': embedding,
        'match_threshold': threshold,
        'match_count': k
    }).execute()
    
    # step 3: return results
    return result.data

def retrieve(
    question: str,
    k: int = settings.top_k_results
) -> list:
    print(f"\n=== Retrieving for: '{question}' ===")

    # step 1: expand
    cleaned = expand_query(question)
    print(f"Cleaned query: '{cleaned}'")
    
    # step 2: enrich
    enriched = enrich_query(cleaned)
    print(f"Enriched query: '{enriched[:80]}...'")
    
    # step 3: search BOTH
    clean_results = search_supabase(cleaned, k=k)
    enriched_results = search_supabase(enriched, k=k)
    
    # step 4: combine + deduplicate
    seen = set()
    combined = []
    
    for result in clean_results + enriched_results:  # ← combine here!
        if result['id'] not in seen:
            seen.add(result['id'])
            combined.append(result)
    
    # step 5: sort by similarity
    combined.sort(
        key=lambda x: x['similarity'],
        reverse=True
    )
    
    print(f"Retrieved {len(combined)} unique chunks")
    return combined