# main.py (位於專案根目錄)

import sys
import logging
from pathlib import Path
from tkinter import messagebox # <--- 【修正一：在這裡導入 messagebox】

# --- 處理模組導入路徑 ---
try:
    from nessus_reporter.app_controller import AppController, IView
    from nessus_reporter.ui.main_window import MainWindow
except ImportError:
    src_path = str(Path(__file__).resolve().parent / 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from nessus_reporter.app_controller import AppController, IView
    from nessus_reporter.ui.main_window import MainWindow


def main():
    """應用程式的主入口點。"""
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log", encoding='utf-8'), # 寫入檔案
            logging.StreamHandler() # 顯示在終端機
        ]
    )

    app_view = None
    try:
        # --- [修正二] 這是現在最清晰的啟動流程 ---
        # 1. 建立控制器，並告訴它要使用哪個 UI 類別
        controller = AppController(view_class=MainWindow)
        
        # 2. 從控制器獲取已建立的 UI 實例
        app_view = controller.view
        
        # 3. 啟動 UI 的主事件迴圈，顯示視窗
        logging.info("應用程式啟動成功，進入主迴圈。")
        app_view.mainloop()

    except Exception as e:
        # 捕捉所有未被處理的嚴重錯誤，包括 AppController 初始化時的 ConfigError
        logging.critical(f"應用程式發生無法恢復的錯誤: {e}", exc_info=True)
        
        # 使用我們剛剛導入的 messagebox 來彈出一個圖形化的錯誤視窗
        messagebox.showerror("嚴重錯誤", f"應用程式意外終止。\n\n詳情: {e}")

if __name__ == "__main__":
    main()