import pdfplumber

pdf_path = "Ghana Constitution.pdf"
try:
    with pdfplumber.open(pdf_path) as pdf:
        # Looking at pages 15 to 25 to see the start of the actual legal text
        for i in range(14, min(25, len(pdf.pages))):
            print(f"--- PAGE {i+1} ---")
            print(pdf.pages[i].extract_text())
            print("\n")
except Exception as e:
    print(f"Error: {e}")
