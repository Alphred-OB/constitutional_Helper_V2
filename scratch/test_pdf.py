import pdfplumber

pdf_path = "Ghana Constitution.pdf"
with pdfplumber.open(pdf_path) as pdf:
    for i in range(70, 80): # Try pages around Article 110
        page = pdf.pages[i]
        text = page.extract_text()
        print(f"--- PAGE {i+1} ---")
        print(text[:500])
        print("\n")
