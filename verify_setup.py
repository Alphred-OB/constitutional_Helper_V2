#!/usr/bin/env python
"""Verification script for Constitutional Helper Setup"""

import sys
import os

print("=" * 60)
print("CONSTITUTIONAL HELPER - VERIFICATION SCRIPT")
print("=" * 60)

# Test 1: Python version
print("\n[1] Python Version Check")
print(f"    Python {sys.version.split()[0]} - OK" if sys.version_info >= (3, 9) else f"    FAIL: Need Python 3.9+")

# Test 2: Config module
print("\n[2] Configuration Module")
try:
    import config
    print(f"    LLM Model: {config.LLM_MODEL} - OK")
    print(f"    RAG Top-N: {config.RAG_TOP_N} - OK")
    print(f"    Threshold: {config.RAG_SIMILARITY_THRESHOLD} - OK")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 3: Core Dependencies
print("\n[3] Core Dependencies")
deps = ['streamlit', 'groq', 'sentence_transformers', 'numpy', 'sklearn']
for dep in deps:
    try:
        __import__(dep)
        print(f"    {dep} - OK")
    except ImportError:
        print(f"    {dep} - MISSING")

# Test 4: RAG Module
print("\n[4] RAG Module Functions")
try:
    from rag import load_chunks, encode_query, search, build_context
    print("    All RAG functions available - OK")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 5: App Validation Functions
print("\n[5] App Validation Functions")
try:
    from app import validate_question, escape_and_format_html
    print("    Validation functions available - OK")
    
    # Test validation
    is_valid, q = validate_question("Test question?")
    print(f"    Question validation working - OK" if is_valid else f"    Question validation issue")
    
    # Test HTML escape
    escaped = escape_and_format_html("<script>test</script>")
    is_safe = "&lt;" in escaped or "&#" in escaped
    print(f"    HTML escaping working - OK" if is_safe else f"    HTML escaping issue")
except Exception as e:
    print(f"    FAIL: {e}")

# Test 6: Environment Variables
print("\n[6] Environment Check")
if os.path.exists('.env'):
    print("    .env file found - OK")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        groq_key = os.environ.get('GROQ_API_KEY')
        if groq_key:
            masked = groq_key[:10] + "..." + groq_key[-4:] if len(groq_key) > 20 else "***"
            print(f"    GROQ_API_KEY set: {masked} - OK")
        else:
            print("    WARNING: GROQ_API_KEY not found in .env")
    except Exception as e:
        print(f"    WARNING: {e}")
else:
    print("    WARNING: .env file not found (needed for production)")

# Test 7: Data Files
print("\n[7] Data Files Check")
files_to_check = ['constitution_chunks.json', 'icons.py']
for fname in files_to_check:
    if os.path.exists(fname):
        size_mb = os.path.getsize(fname) / (1024 * 1024)
        print(f"    {fname}: {size_mb:.2f}MB - OK")
    else:
        print(f"    {fname} - MISSING")

# Test 8: Documentation
print("\n[8] Documentation Check")
docs = ['SETUP.md', 'CODE_REVIEW.md', 'SYSTEM_DOCUMENTATION.md']
for doc in docs:
    if os.path.exists(doc):
        size_kb = os.path.getsize(doc) / 1024
        print(f"    {doc}: {size_kb:.1f}KB - OK")
    else:
        print(f"    {doc} - MISSING")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
