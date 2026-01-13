from pypdf import PdfReader
import os

files = [
    "Manual de Recarga de Munições Revista Magnum .pdf",
    "manual recarga.pdf",
    "tabela imbelll.pdf"
]

for f in files:
    if os.path.exists(f):
        try:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages[:3]: # Check first 3 pages
                text += page.extract_text()
            
            print(f"--- {f} ---")
            if len(text.strip()) > 50:
                print(f"Text found ({len(text)} chars). Snippet: {text[:200]}...")
            else:
                print("No significant text found (likely image-based).")
        except Exception as e:
            print(f"Error reading {f}: {e}")
    else:
        print(f"File not found: {f}")
