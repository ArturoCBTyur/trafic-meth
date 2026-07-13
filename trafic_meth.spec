# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para el Simulador de Tráfico 2D.

Produce un ejecutable de UN SOLO ARCHIVO (onefile) autocontenido: no requiere
instalar Python ni dependencias. El mismo .spec se usa en Windows, macOS y Linux
(PyInstaller construye para el SO en el que corre — no hace cross-compilación).

    pyinstaller --clean -y trafic_meth.spec
    -> dist/SmartIntersection (o SmartIntersection.exe en Windows)
"""

block_cipher = None

a = Analysis(
    ["frontend.py"],
    pathex=[],
    binaries=[],
    datas=[],
    # Módulos locales + libs (aunque PyInstaller los detecta, se listan por robustez)
    hiddenimports=[
        "numerical_engine",
        "music",
        "modulo_explicativo",
        "pygame",
        "numpy",
        "openpyxl",
        "openpyxl.chart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="SmartIntersection",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # deja visible la consola: muestra rutas de Excel y logs [INFO]
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS: permite abrir por doble clic correctamente
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
