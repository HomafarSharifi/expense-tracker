# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.building.build_main import Analysis, COLLECT, EXE, PYZ


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=["matplotlib.backends.backend_qtagg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pandas", "pyarrow", "mysql.connector"],
    noarchive=False,
    optimize=0,
)

# Windows API-set contracts (api-ms-win-*.dll) are OS shims. PyInstaller can
# find unrelated copies on PATH and bundle them beside Qt. Private media-tool
# DLL folders can also supply incompatible ICU libraries, which QtCore needs.
a.binaries = [
    binary
    for binary in a.binaries
    if not os.path.basename(binary[0]).lower().startswith("api-ms-win-")
    and "\\.cache\\codex-runtimes\\".lower() not in binary[1].lower()
]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ExpenseTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/expense-tracker.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ExpenseTracker",
)
