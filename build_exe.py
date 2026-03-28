#!/usr/bin/env python3
"""Build a single-file executable for LLM Usage Tracker.

Usage:
    pip install -r requirements.txt pyinstaller
    python build_exe.py

Produces: dist/LLM-Usage-Tracker.exe (Windows) or dist/LLM-Usage-Tracker (Linux/Mac)
"""

import os
import PyInstaller.__main__
import platform
import sys

args = [
    "run.py",
    "--onefile",
    "--name=LLM-Usage-Tracker",
    "--windowed",
    # Bundle the icon assets into the executable
    "--add-data=assets:assets",
    # Hidden imports that PyInstaller can miss
    "--hidden-import=curl_cffi",
    "--hidden-import=curl_cffi.requests",
    "--hidden-import=curl_cffi.const",
    "--hidden-import=browser_cookie3",
    "--hidden-import=cryptography",
    "--hidden-import=cryptography.fernet",
    "--hidden-import=cryptography.hazmat.primitives.kdf.pbkdf2",
    "--hidden-import=PyQt5",
    "--hidden-import=PyQt5.sip",
    "--hidden-import=PyQt5.QtCore",
    "--hidden-import=PyQt5.QtGui",
    "--hidden-import=PyQt5.QtWidgets",
    # Collect all files from curl_cffi (includes .dll/.so native libs)
    "--collect-all=curl_cffi",
    "--collect-all=browser_cookie3",
    "--collect-all=certifi",
    # Don't prompt on overwrite
    "--noconfirm",
]

# Windows: use .ico for taskbar icon
if platform.system() == "Windows":
    ico = os.path.join("assets", "icon.ico")
    if os.path.exists(ico):
        args.append(f"--icon={ico}")
    # Windows uses ; as path separator in --add-data
    for i, a in enumerate(args):
        if a.startswith("--add-data="):
            args[i] = a.replace(":", ";", 1)

print(f"Building for {platform.system()} {platform.machine()}...")
print(f"Python {sys.version}")
print()

PyInstaller.__main__.run(args)

print()
print("Build complete! Executable is in the dist/ folder.")
