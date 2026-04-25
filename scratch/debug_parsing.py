import pdfplumber

with pdfplumber.open("Ghana Constitution.pdf") as pdf:
    for i in range(15, 25):
        page = pdf.pages[i]
        print(f"--- PAGE {i+1} ---")
        print(page.extract_text())
        print("\n")
