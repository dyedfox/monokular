# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None
root = os.path.abspath(os.path.dirname(SPECPATH))

a = Analysis(
    [os.path.join(root, 'main.py')],
    pathex=[root],
    binaries=[],
    datas=[
        (os.path.join(root, 'assets', 'icon.svg'), 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='monokular',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    icon=os.path.join(root, 'assets', 'icon.svg'),
)
