def check_raw_text():
    from langchain_community.document_loaders import PyPDFLoader
    
    loader = PyPDFLoader("backend/data/constitution.pdf")
    pages = loader.load()
    
    # find article 120 in raw text
    for i, page in enumerate(pages):
        if "120." in page.page_content:
            print(f"=== Page {i} ===")
            idx = page.page_content.find("120.")
            print(repr(page.page_content[max(0, idx-50):idx+100]))
            print()

if __name__ == "__main__":
    check_raw_text()