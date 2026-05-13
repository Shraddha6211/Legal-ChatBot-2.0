from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys (from .env)
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str = "nepal-constitution"
    pinecone_environment: str = "us-east-1"
    redis_url: str = "redis://localhost:6379"
    
    # LLM Config
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    
    # Retrieval Config
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 12
    similarity_threshold: float = 0.35
    
    # Memory Config
    max_history_messages: int = 10
    cache_ttl_seconds: int = 3600      # 1 hour
    session_ttl_seconds: int = 86400   # 24 hours
    
    # PDF Config
    pdf_path: str = "backend/data/constitution.pdf"
    
    class Config:
        env_file = ".env"

# single instance used everywhere!
settings = Settings()