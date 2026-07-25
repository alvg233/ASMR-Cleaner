# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ASMR-Cleaner — ONEDIR mode (instant startup).
Build: pyinstaller build_onedir.spec
Output: dist/ASMR-Cleaner/  (folder, zip for distribution)
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pydub', 'numpy', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'pandas', 'PIL', 'cv2', 'tensorflow', 'torch',
        'librosa', 'soundfile', 'scipy',
        'mkl', 'mkl-service',  # Anaconda MKL — excluded if using pip numpy
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ASMR-Cleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ASMR-Cleaner',
)
