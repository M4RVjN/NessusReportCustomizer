# -*- mode: python ; coding: utf-8 -*-
# 最後修改時間：2025/06/28
# 使用 'pyinstaller NessusTool-Marvin.spec' 指令來進行打包。

block_cipher = None

# --- Analysis Section ---
# 告訴 PyInstaller 如何分析您的專案
a = Analysis(
    ['main.py'],
    # [修改] 告訴 PyInstaller 您的原始碼在 'src' 目錄下
    pathex=['src'],
    binaries=[],
    # [修改] 告訴 PyInstaller 要將哪些額外檔案打包進去
    datas=[
        ('config.yaml', '.'),
        ('resources/icons/IE.ico', 'resources/icons') # 假設圖示路徑
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

# --- PYZ Section ---
# 建立一個包含所有 Python 模組的 .pyz 存檔
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- EXE Section ---
# 這是定義最終 .exe 檔案的核心部分
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NessusTool-Marvin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # [修改] console=False 等同於 --windowed，用於 GUI 應用
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # [修改] 在這裡指定圖示路徑，比在指令中更穩定
    icon='resources/icons/IE.ico',
)

# --- [修改] 將其定義為單一檔案模式 ---
# 透過移除 COLLECT 部分，只保留 EXE，來實現 --onefile 的效果
coll = None
