import pdfplumber

pdf_path = "Ghana Constitution.pdf"
try:
    with pdfplumber.open(pdf_path) as pdf:
        # Looking at pages 20 to 23 to see Article headers
        for i in range(19, 23):
            print(f"--- PAGE {i+1} ---")
            print(pdf.pages[i].extract_text())
            print("\n")
except Exception as e:
    print(f"Error: {e}")
