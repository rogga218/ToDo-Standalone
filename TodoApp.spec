import os

SPECPATH = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(SPECPATH, 'src', 'main.py')],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, 'src'), 'src'),
        (os.path.join(SPECPATH, 'src', 'assets'), 'src/assets'),
    ],
    hiddenimports=['uvicorn', 'pydantic_settings', 'python_multipart', '_cffi_backend', 'cffi', 'PySide6.QtWebEngineWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TodoApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(SPECPATH, 'src', 'assets', 'logo.ico')],
)
