# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec for ASMR-Cleaner.
Build command: pyinstaller build_exe.spec
Output: dist/ASMR-Cleaner.exe (single file)
"""

import sys
from pathlib import Path

# --- ffmpeg / ffprobe binary paths ---
# Put ffmpeg.exe and ffprobe.exe in the project root.
_FFMPEG = Path("ffmpeg.exe")
_FFPROBE = Path("ffprobe.exe")
_binaries = []
if _FFMPEG.exists():
    _binaries.append((str(_FFMPEG), '.'))
if _FFPROBE.exists():
    _binaries.append((str(_FFPROBE), '.'))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=_binaries,
    datas=[],
    hiddenimports=['pydub', 'numpy', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'pandas', 'PIL', 'cv2', 'tensorflow', 'torch',
        'librosa', 'soundfile', 'scipy',  # we don't use these
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ASMR-Cleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # GUI 应用，不显示命令行窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                  # 如果你有 .ico 图标，填路径
)
