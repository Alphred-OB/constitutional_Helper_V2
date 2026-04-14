# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Constitutional Helper

from PyInstaller.utils.hooks import collect_submodules
import os

# Collect all submodules for sentence-transformers and torch
hiddenimports = collect_submodules('sentence_transformers')
hiddenimports += collect_submodules('torch')
hiddenimports += [
    'streamlit',
    'groq',
    'gtts',
    'sklearn',
    'numpy',
    'dotenv',
    'deep_translator',
]

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('constitution_chunks.json', '.'),
        ('constitution_embeddings.pkl', '.'),
        ('styles.css', '.'),
        ('.streamlit', '.streamlit'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ConstitutionalHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Optional: add an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ConstitutionalHelper',
)
