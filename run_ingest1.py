# # add to run_ingest.py temporarily:
# from backend.db.supabase_client import get_supabase_client

# def verify_ingestion():
#     supabase = get_supabase_client()
    
#     # check total rows
#     result = supabase.table("documents")\
#         .select("id, article_number, title, part_number")\
#         .order("article_number")\
#         .limit(10)\
#         .execute()
    
#     print("=== First 10 Articles in Supabase ===")
#     for row in result.data:
#         print(f"Article {row['article_number']}: "
#               f"{row['title'][:50]} "
#               f"(Part {row['part_number']})")
    
#     # check total count
#     count = supabase.table("documents")\
#         .select("id", count="exact")\
#         .execute()
#     print(f"\nTotal documents: {count.count}")
    
#     # check specific article 18
#     art18 = supabase.table("documents")\
#         .select("article_number, title, content")\
#         .eq("article_number", 18)\
#         .execute()
    
#     print(f"\n=== Article 18 ===")
#     if art18.data:
#         print(f"Title: {art18.data[0]['title']}")
#         print(f"Preview: {art18.data[0]['content'][:200]}")
#     else:
#         print("Article 18 NOT FOUND! ❌")

# if __name__ == "__main__":
#     verify_ingestion()


# ADDITION
def diagnose_chunks():
    from backend.core.ingest import load_pdf, chunk_by_article
    from config import settings
    
    full_text, page_map = load_pdf(settings.pdf_path)
    documents = chunk_by_article(full_text, page_map)
    
    print("=== Checking Article Numbers ===")
    prev_num = 0
    for doc in documents:
        curr_num = doc.metadata['article_number']
        # flag suspicious jumps
        if curr_num < prev_num:
            print(f"⚠️  Number went BACKWARDS: {prev_num} → {curr_num}")
            print(f"   Title: {doc.metadata['title']}")
            print(f"   Preview: {doc.page_content[:100]}")
            print()
        prev_num = curr_num

if __name__ == "__main__":
    diagnose_chunks()