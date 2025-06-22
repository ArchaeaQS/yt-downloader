# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'customtkinter',
        'requests',
        'asyncio',
        'pathlib',
        'subprocess',
        'json',
        'threading',
        'concurrent.futures',
        'collections.abc',
        'ui.main_window',
        'ui.components',
        'ui.theme',
        'download.manager',
        'download.retry_handler',
        'utils.cookie_manager',
        'tool_manager',
        'config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy', 
        'pandas',
        'scipy',
        'PIL',
        'pytest',
        'unittest',
        'test',
        'tests',
    ],
    noarchive=False,
    optimize=0,
)

# onefile形式（推奨）: 単一の実行ファイル
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='yt_downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # GUIアプリケーション：コンソールウィンドウを表示しない
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                  # 必要に応じてアイコンファイルのパスを指定
)

# onedir形式に変更する場合は以下をアンコメント:
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='yt_downloader'
# )
