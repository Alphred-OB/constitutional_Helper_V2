import pdfplumber
import sys

pdf_path = "Ghana Constitution.pdf"
try:
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(min(10, len(pdf.pages))):
            print(f"--- PAGE {i+1} ---")
            print(pdf.pages[i].extract_text())
            print("\n")
except Exception as e:
    print(f"Error: {e}")
