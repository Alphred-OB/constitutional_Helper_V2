import pdfplumber
import re
import json

def clean_text(text):
    if not text: return ""
    text = text.strip()
    # Basic cleanup of weird characters
    text = text.replace("", "")
    return text

def rebuild():
    pdf_path = "Ghana Constitution.pdf"
    full_text = []
    
    print(f"Reading {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Skip first 20 pages (TOC and front matter)
            if i < 21: continue
            text = page.extract_text()
            if text:
                full_text.append(text)
    
    content = "\n".join(full_text)
    
    # Split by Article numbers: digit(s) followed by a dot at start of line
    # Regex: \n(\d+)\.
    # We use a positive lookahead to keep the article number
    # Actually, we'll split and keep the numbers
    pattern = r'\n(?=\d+\.\s+[A-Z])'
    articles = re.split(pattern, content)
    
    chunks = []
    current_chapter = "Unknown"
    
    for art in articles:
        art = art.strip()
        if not art: continue
        
        # Detect Chapter change
        chapter_match = re.search(r'CHAPTER\s+([A-Z\s]+)', art)
        if chapter_match:
            current_chapter = f"CHAPTER {chapter_match.group(1).strip()}"
            
        # Detect Article info
        # e.g., "12. Title\nContent"
        match = re.match(r'^(\d+)\.\s+([A-Z].+?)\n(.+)', art, re.DOTALL)
        if match:
            art_num = match.group(1)
            art_title = match.group(2).strip()
            art_text = match.group(3).strip()
            
            chunks.append({
                "chapter": current_chapter,
                "article": f"Article {art_num}: {art_title}",
                "text": art_text
            })
        else:
            # Fallback for weirdly formatted articles or headers
            if len(art) > 100:
                chunks.append({
                    "chapter": current_chapter,
                    "article": "General Provisions",
                    "text": art
                })
                
    output_path = "constitution_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4)
        
    print(f"Rebuilt {len(chunks)} chunks.")

if __name__ == "__main__":
    rebuild()
