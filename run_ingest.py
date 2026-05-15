# legal-chatbot-v2/run_ingest.py

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.core.ingest import run_ingestion

if __name__ == "__main__":
    run_ingestion()

def check_part_format():
    from backend.core.ingest import load_pdf
    from config import settings
    
    full_text, page_map = load_pdf(settings.pdf_path)
    
    # find all "Part" occurrences
    import re
    matches = re.finditer(
        r'Part[\s-]+\d+[^\n]*\n[^\n]*',
        full_text,
        re.IGNORECASE
    )
    
    print("=== Part Patterns Found in PDF ===")
    for match in matches:
        print(repr(match.group()))
        print()

if __name__ == "__main__":
    check_part_format()