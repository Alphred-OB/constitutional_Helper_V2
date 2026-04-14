#!/usr/bin/env python
"""
Setup verification script - Verify all dependencies are installed and configured correctly.
Run this before building the .exe or deploying to cloud.
"""

import sys
import os
import subprocess

def check_python_version():
    """Verify Python 3.9+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_required_files():
    """Check all required files exist"""
    required = [
        "app.py",
        "config.py",
        "rag.py",
        "constitution_chunks.json",
        "constitution_embeddings.pkl",
        "styles.css",
        "requirements.txt",
    ]
    
    missing = []
    for file in required:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print(f"✓ All {len(required)} required files present")
    return True

def check_packages():
    """Verify all packages from requirements.txt are installed"""
    try:
        import streamlit
        import groq
        import sentence_transformers
        import sklearn
        import gtts
        import deep_translator
        import pdfplumber
        print("✓ All core packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("\nInstall with: pip install -r requirements.txt")
        return False

def check_env_vars():
    """Check environment variables"""
    from dotenv import load_dotenv
    load_dotenv()
    
    key = os.getenv("GROQ_API_KEY")
    if not key:
        print("⚠ GROQ_API_KEY not set (required for cloud mode)")
        print("  Set in .env file or Streamlit secrets")
        return True  # Not critical for local testing
    else:
        print("✓ GROQ_API_KEY configured")
        return True

def check_models():
    """Test model loading"""
    try:
        from sentence_transformers import SentenceTransformer
        print("  Loading embedding model... (this may take a moment)")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✓ Embedding model loaded successfully")
        return True
    except Exception as e:
        print(f"⚠ Warning: Could not load model: {e}")
        print("  This is normal on first run - model will download when app starts")
        return True

def main():
    print("\n" + "="*60)
    print("Constitutional Helper - Setup Verification")
    print("="*60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Python Packages", check_packages),
        ("Environment Config", check_env_vars),
        ("Model Loading", check_models),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}")
        print("-" * 40)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    if all(results):
        print("✓ All checks passed! Ready to deploy.")
        print("\nNext steps:")
        print("  Local testing:  streamlit run app.py")
        print("  Deploy online:  git push (then deploy on Streamlit Cloud)")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
