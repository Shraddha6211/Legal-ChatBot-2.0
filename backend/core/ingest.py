# backend/core/ingest.py

import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from backend.db.supabase_client import get_supabase_client
from config import settings
import supabase

def load_pdf(filepath: str) -> str:
    """
    Load PDF and return:
    1. full_text: complete text for chunking
    2. page_map: {page_number: text} for metadata
    """
    loader = PyPDFLoader(filepath)
    pages = loader.load()
    
    full_text = ""
    page_map = {}
    
    for page in pages:
        page_num = page.metadata.get("page", 0) + 1  # 0-indexed → 1-indexed
        page_text = page.page_content
        
        page_map[page_num] = page_text    # store for metadata lookup
        full_text += page_text + "\n"     # combine for chunking
    
    print(f"Loaded {len(pages)} pages")
    return full_text, page_map

# LOAD PAGE NUMBER
def find_page_number(chunk_text: str, page_map: dict) -> int:
    search_text = chunk_text[:50].strip()
    for page_num, page_text in page_map.items():
        if search_text in page_text:
            return page_num
    return 0

# CHUNKING the document on the basis of parts in the constiution and article number

def chunk_by_article(
        full_text: str, 
        page_map: dict,
        source: str = "constitution.pdf",
        skip_pages: int = 5
    ) -> list:
    
    # step 1: skip first N pages(TOC)
    # Rebuild full_text without TOC pages
    filtered_text = ""
    for page_num, page_text in page_map.items():
        if page_num > skip_pages:
            filtered_text = filtered_text + page_text + "\n"

    print(f"Skippeddd first {skip_pages} pages (TOC)")

    # step 2: Split by article pattern
    pattern = r'\n(?=\d+\.\s+[A-Z])'
    raw_chunks = re.split(pattern, filtered_text)
    print(f"Raw chunks after split: {len(raw_chunks)}")

    # step 3: Track current part
    current_part_number = 0
    current_part_name = "Preamble"
    part_pattern = re.compile(
        r'Part[\s-]+(\d+)\s*\n?([^\n]+)?',
        re.IGNORECASE
    )
    article_pattern = re.compile(r'^(\d+)\.\s+(.+)')

    documents = []

    for chunk in raw_chunks:
        chunk = chunk.strip()

        # skip TOC/ short chunks
        if len(chunk) < 200:
            continue
        if len(chunk.split()) < 20:
            continue

        # Check if chunk contains part boundary
        part_match = part_pattern.search(chunk)
        if part_match:
            current_part_number = int(part_match.group(1))
            current_part_name = part_match.group(2).strip() \
                if part_match.group(2) else ""
            print(f"Part {current_part_number}: {current_part_name}")

        # extract article number and title
        first_line = chunk.split('\n')[0].strip()
        article_match = article_pattern.match(first_line)
        
        if not article_match:
            continue    # skip non-article chunks!
        
        article_number = int(article_match.group(1))
        article_title = article_match.group(2).strip()
        
        # get content (everything after first line)
        lines = chunk.split('\n')
        content = '\n'.join(lines[1:]).strip()

        # skip heading-only chunks
        if len(content) < 100:
            continue
        
        # find page number
        page_number = find_page_number(chunk, page_map)

        # create LangChain Document!
        doc = Document(
            page_content=chunk,
            metadata={
                "article_number": article_number,
                "title": article_title,
                "part_number": current_part_number,
                "part_name": current_part_name,
                "source": source,
                "page_number": page_number,
                "chunk_length": len(chunk),
                "word_count": len(chunk.split())
            }
        )
        documents.append(doc)
    
    print(f"Total meaningful documents: {len(documents)}")
    return documents

# INSERT TO SUPABASE
# Documents → Embeddings → Supabase
def upsert_to_supabase(documents: list, index, batch_size: int = 100) -> None:
    """
    Generate embeddings and upsert to Supabase
    """
    embeddings_model = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key
    )
    
    # step 1: extract text from documents
    # hint: [doc.page_content for doc in documents]
    texts = [doc.page_content for doc in documents]
    print(f"Generating embeddings for {len(texts)} documents...")
    
    # step 2: generate embeddings
    # hint: embeddings_model.embed_documents(texts)
    embeddings = embeddings_model.embed_documents(texts)
    print(f"Embeddings generated: {len(embeddings)}")
    
    # step 3: get supabase client
    
    # step 4: Prepare rows for supabase
    rows = []
    for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
        rows.append({
            "id": f"article-{doc.metadata['article_number']}-{i}",
            "content": doc.page_content,
            "embedding": embedding,
            "article_number": doc.metadata["article_number"],
            "title": doc.metadata["title"],
            "part_number": doc.metadata["part_number"],
            "part_name": doc.metadata["part_name"],
            "source": doc.metadata["source"],
            "page_number": doc.metadata["page_number"],
            "chunk_length": doc.metadata["chunk_length"],
            "word_count": doc.metadata["word_count"]
        })

    # step 5: upsert in batches:
    total_batches = (len(rows) // batch_size) + 1

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("documents").upsert(batch).execute()
        print(f"Upserted batch {i//batch_size + 1}/{total_batches}")

    print(f"All {len(rows)} documents upserted to Supabase!")


## MAIN FUNCTION 
def run_ingestion(pdf_path: str = settings.pdf_path):
    """
    Complete ingestion pipeline:
    PDF → chunks → embeddings → Supabase
    """
    print("=== Starting Ingestion Pipeline ===")
    
    # step 1: load PDF
    print("Loading PDF...")
    full_text, page_map = load_pdf(pdf_path)
    print(f"Pages loaded: {len(page_map)}")
    
    # step 2: chunk by article
    print("Chunking by article...")
    documents = chunk_by_article(full_text, page_map)
    print(f"Documents created: {len(documents)}")
    
    # step 3: preview first 3 documents
    print("\nFirst 3 document previews:")
    for doc in documents[:3]:
        print(f"Article {doc.metadata['article_number']}: "
              f"{doc.metadata['title'][:50]}")
        print(f"Part {doc.metadata['part_number']}: "
              f"{doc.metadata['part_name']}")
        print(f"Page: {doc.metadata['page_number']}")
        print(f"Preview: {doc.page_content[:100]}")
        print()
    
    # step 4: upsert to Supabase
    print("Upserting to Supabase...")
    upsert_to_supabase(documents)
    
    print("=== Ingestion Complete! ===")
    return len(documents)


if __name__ == "__main__":
    run_ingestion()
