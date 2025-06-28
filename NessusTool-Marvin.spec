# NessusTool-Marvin.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析您的專案
a = Analysis(
    ['main.py'],
    pathex=['src'],  # 【關鍵】告訴 PyInstaller 您的原始碼在 'src' 目錄下
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        # 【修改】直接將 IE.ico 放到根目錄 '.'，而不是子目錄
        ('resources/icons/IE.ico', '.') 
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 建立包含 Python 模組的 .pyz 存檔
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 定義最終的 .exe 檔案
exe = EXE(
    pyz,
    a.scripts,
    [], # 我們使用 onefile 模式，所以這裡留空
    exclude_binaries=True,
    name='NessusTool-Marvin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 等同於 --windowed，不顯示黑色命令視窗
    icon='resources/icons/IE.ico', # 【關鍵】在這裡指定您的圖示路徑
)

# 【關鍵】定義為單一檔案模式
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NessusTool-Marvin',
)
