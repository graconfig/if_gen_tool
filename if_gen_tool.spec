# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

added_datas = []
added_datas += collect_data_files('customtkinter')
added_datas += [('locale', 'locale')]

hidden_imports = []
hidden_imports += collect_submodules('hana_ml')
hidden_imports += collect_submodules('sap_ai_sdk_gen')
hidden_imports += collect_submodules('google.cloud.aiplatform')
hidden_imports += collect_submodules('google.genai')
hidden_imports += collect_submodules('aioboto3')
hidden_imports += collect_submodules('aiobotocore')
hidden_imports += [
    'pkg_resources.py2_warn',
    'charset_normalizer.md__mypyc',
    'grpc',
    'google.protobuf',
    '_cffi_backend',
    'cffi',
    'cryptography',
]

a = Analysis(
    ['gui_main.py'],
    pathex=[],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'notebook'],
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
    name='if_gen_tool',
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
    icon=None,
)
