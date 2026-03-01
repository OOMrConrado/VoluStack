# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['volustack/main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/icon.ico', 'assets')],
    hiddenimports=['comtypes.stream', 'pycaw.pycaw', 'qtawesome'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'xmlrpc', 'pydoc',
        'PyQt6.QtWebEngine', 'PyQt6.Qt3D', 'PyQt6.QtMultimedia',
        'PyQt6.QtBluetooth', 'PyQt6.QtNfc', 'PyQt6.QtSensors',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='volustack',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='VoluStack',
)
