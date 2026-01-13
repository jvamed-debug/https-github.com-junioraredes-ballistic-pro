import os
from pypdf import PdfReader

def analyze_pdf(filepath):
    print(f"--- Analyzing: {os.path.basename(filepath)} ---")
    try:
        reader = PdfReader(filepath)
        number_of_pages = len(reader.pages)
        print(f"Total Pages: {number_of_pages}")
        
        # Read first 3 pages to get header/intro info
        for i in range(min(3, number_of_pages)):
            page = reader.pages[i]
            text = page.extract_text()
            print(f"\n[Page {i+1} Sample]\n{text[:500]}...") # Print first 500 chars
            
        # Try to find a page with tabular data (looking for keywords)
        keywords = ["Caliber", "Bullet", "Powder", "Start", "Max", "Grains", "Vel"]
        found_data_page = False
        for i in range(min(20, number_of_pages)): # Search first 20 pages
            page = reader.pages[i]
            text = page.extract_text()
            if any(k in text for k in keywords):
                print(f"\n[Potential Data Page {i+1}]\n{text[:1000]}")
                found_data_page = True
                break
        
        if not found_data_page:
            print("Could not identify a clear data page in the first 20 pages.")

    except Exception as e:
        print(f"Error reading PDF: {e}")
    print("\n" + "="*50 + "\n")

files = [
    "Manual de Recarga de Munições Revista Magnum .pdf",
    "manual recarga.pdf",
    "manual-de-recarga-cbc.pdf",
    "tabela imbelll.pdf"
]

for f in files:
    analyze_pdf(f)
