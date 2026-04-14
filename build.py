#!/usr/bin/env python
"""
Build script to create standalone Windows executable.
Usage: python build.py
"""

import os
import sys
import subprocess
import shutil

def build_exe():
    """Build standalone executable using PyInstaller"""
    
    print("=" * 60)
    print("Constitutional Helper - Building Standalone Executable")
    print("=" * 60)
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        sys.exit(1)
    
    # Check if spec file exists
    if not os.path.exists("build_exe.spec"):
        print("ERROR: build_exe.spec not found!")
        sys.exit(1)
    
    # Check if required files exist
    required_files = [
        "app.py",
        "config.py",
        "rag.py",
        "constitution_chunks.json",
        "constitution_embeddings.pkl",
        "styles.css",
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"ERROR: Missing required files: {', '.join(missing)}")
        sys.exit(1)
    
    print("✓ All required files found")
    print("✓ PyInstaller ready")
    print()
    
    # Clean previous builds
    if os.path.exists("dist"):
        print("Cleaning previous build...")
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Run PyInstaller
    print("Building executable (this may take 2-5 minutes)...")
    print()
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "build_exe.spec",
        "--distpath", "dist",
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print()
        print("ERROR: Build failed!")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✓ Build Complete!")
    print("=" * 60)
    print()
    print("Executable location:")
    print("  dist/ConstitutionalHelper/ConstitutionalHelper.exe")
    print()
    print("To run: Double-click dist/ConstitutionalHelper/ConstitutionalHelper.exe")
    print()
    print("Note: First run may take 10-30 seconds to initialize models.")
    print()

if __name__ == "__main__":
    build_exe()
