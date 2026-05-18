import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.core.retriever import retrieve

def test_retrieval():
    questions = [
        "What is the right to equality?",
        "How is the President elected?",
        "What are the duties of citizens?"
    ]
    
    for question in questions:
        results = retrieve(question)
        print(f"\nQuestion: '{question}'")
        print(f"Results: {len(results)}")
        for r in results[:3]:
            print(f"  Article {r['article_number']}: "
                  f"{r['title'][:50]} "
                  f"(similarity: {r['similarity']:.3f})")

if __name__ == "__main__":
    test_retrieval()