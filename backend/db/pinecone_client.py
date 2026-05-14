# backend/db/pinecone_client.py

from pinecone import Pinecone, ServerlessSpec
from config import settings

def get_pinecone_index():
    # step 1: initialize pinecone client
    pc = Pinecone(api_key=settings.pinecone_api_key)
    
    # step 2: check if index exists
    existing_indexes = pc.list_indexes().names()
    print(f"Existing indexes: {existing_indexes}")
    
    # step 3: create if not exists
    if settings.pinecone_index_name not in existing_indexes:
        print(f"Creating index: {settings.pinecone_index_name}")
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimension,  # 1536!
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=settings.pinecone_environment
            )
        )
        print("Index created!")
    else:
        print(f"Index already exists!")
    
    # step 4: return index reference
    return pc.Index(settings.pinecone_index_name)