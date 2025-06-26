# src/nessus_reporter/app_controller.py

import sys
import os
import logging
import threading
import queue
import time
from pathlib import Path
from typing import List, Optional, Any
from abc import ABC, abstractmethod

# 導入我們所有的核心元件和型別
from .core.config_manager import ConfigurationManager, ConfigError, FieldConfig
from .core.processor import BatchProcessor, ParsingError, BatchProcessingResult
from .core.generator import ExcelReportGenerator, ReportGenerationError

# --- 【新增這個輔助函式】 ---
def resource_path(relative_path: str) -> Path:
    """
    獲取資源檔案的絕對路徑。
    在開發環境和 PyInstaller 打包後的環境中都能正常運作。
    """
    try:
        # PyInstaller 會建立一個臨時資料夾，並將路徑儲存在 _MEIPASS 中
        base_path = Path(sys._MEIPASS)
    except Exception:
        # 在開發環境中，sys._MEIPASS 不存在，我們會使用目前的檔案路徑
        base_path = Path(".").resolve()

    return base_path / relative_path

# --- 定義一個抽象的 View 介面 (Interface) ---
class IView(ABC):
    """定義了所有 View 類別必須實現的「合約」。"""
    @abstractmethod
    def show_error(self, title: str, message: str) -> None: pass
    
    @abstractmethod
    def show_info(self, title: str, message: str) -> None: pass

    @abstractmethod
    def update_status(self, text: str) -> None: pass

    @abstractmethod
    def update_progress(self, current: int, total: int) -> None: pass

    @abstractmethod
    def set_ui_state(self, is_enabled: bool) -> None: pass
    
    @abstractmethod
    def get_selected_columns(self) -> List[str]: pass

    @abstractmethod
    def ask_for_input_folder(self) -> Optional[Path]: pass

    @abstractmethod
    def ask_for_output_path(self) -> Optional[Path]: pass

# --- 模擬的 UI 類別，它實現了 IView 介面 ---
class MockMainWindow(IView):
    """一個模擬的 UI 主視窗，用於 AppController 的獨立執行和測試。"""
    def __init__(self, controller: Optional['AppController'] = None):
        self.controller = controller
        print("[UI] 模擬視窗已建立。")

    def show_error(self, title: str, message: str): print(f"--- [UI ERROR] ---\n標題: {title}\n訊息: {message}\n------------------")
    def show_info(self, title: str, message: str): print(f"--- [UI INFO] ---\n標題: {title}\n訊息: {message}\n-----------------")
    def update_status(self, text: str): print(f"[UI STATUS] -> {text}")
    def update_progress(self, current: int, total: int): print(f"[UI PROGRESS] -> {current}/{total} ({(current / total) * 100:.1f}%)")
    def set_ui_state(self, is_enabled: bool): print(f"[UI STATE] -> 主要按鈕已設為: {'啟用' if is_enabled else '禁用'}")
    def get_selected_columns(self) -> List[str]: 
        if self.controller:
            return [f['displayName'] for f in self.controller.fields_config[:3]]
        return []
    def ask_for_input_folder(self) -> Optional[Path]: return Path('data/input')
    def ask_for_output_path(self) -> Optional[Path]: 
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        return output_dir / "Generated_Nessus_Report.xlsx"

class AppController:
    """應用程式的主控制器（大腦）。"""

    # [最終優化] __init__ 接收一個 View 的「類別」，而不是「實例」
    def __init__(self, view_class: type[IView]):
        """
        初始化 AppController。

        Args:
            view_class (type[IView]): 一個符合 IView 介面的 UI 類別，例如 MainWindow。
        """
        self.view: IView
        self.config_manager: Optional[ConfigurationManager] = None
        self.fields_config: List[FieldConfig] = []
        self.processing_lock = threading.Lock()
        self.ui_queue = queue.Queue()

        try:
            # 步驟一：【先】載入設定檔。
            # 【修改】使用 resource_path() 來找到 config.yaml
            config_file_path = resource_path('config.yaml')
            self.config_manager = ConfigurationManager.from_file(config_file_path)
            self.fields_config = self.config_manager.get_all_fields()

            # 步驟二：【後】使用傳入的類別，建立 View 的實例。
            # 這樣 View 在初始化時，Controller 就已經準備好設定資料了。
            self.view = view_class(self)

        except ConfigError as e:
            # 如果設定檔載入失敗，直接向上拋出例外。
            # 讓主程式入口 (main.py) 來決定如何向使用者顯示這個致命錯誤。
            logging.critical(f"設定檔載入失敗，將中止應用程式: {e}")
            raise # 向上拋出，中止 __init__ 流程

    def start_processing(self):
        """由 UI 觸發，開始整個處理流程。"""
        if not self.processing_lock.acquire(blocking=False):
            self.ui_queue.put(("show_info", "提示", "目前有任務正在執行中，請稍候。"))
            return

        input_folder = self.view.ask_for_input_folder()
        if not input_folder:
            self.processing_lock.release()
            return

        output_path = self.view.ask_for_output_path()
        if not output_path:
            self.processing_lock.release()
            return
            
        selected_columns = self.view.get_selected_columns()
        if not selected_columns:
            self.ui_queue.put(("show_error", "錯誤", "請至少選擇一個要匯出的欄位。"))
            self.processing_lock.release()
            return
        
        self.ui_queue.put(("set_ui_state", False))
        self.ui_queue.put(("update_status", f"開始處理資料夾: {input_folder.name}..."))

        processing_thread = threading.Thread(
            target=self._run_batch_task,
            args=(input_folder, output_path, selected_columns)
        )
        processing_thread.start()

    def _run_batch_task(self, input_folder: Path, output_path: Path, selected_columns: List[str]):
        """這個方法會在背景執行緒中執行。"""
        try:
            result = BatchProcessor.process_folder(
                input_folder, self.fields_config, progress_callback=self._progress_update_handler
            )
            
            if not result.dataframe.empty:
                self.ui_queue.put(("update_status", "解析完成，正在生成 Excel 報告..."))
                ExcelReportGenerator.generate_report(result.dataframe, selected_columns, output_path)
                self.ui_queue.put(("update_status", "報告生成成功！"))
                self.ui_queue.put(("show_info", "完成", f"報告已成功儲存至:\n{output_path.resolve()}"))
            else:
                self.ui_queue.put(("update_status", "處理完成，但沒有可生成的資料。"))

            if result.errors:
                logging.warning(f"處理過程中發生了 {len(result.errors)} 個錯誤。")

        except (ParsingError, ReportGenerationError, Exception) as e:
            logging.error(f"處理過程中發生嚴重錯誤: {e}")
            self.ui_queue.put(("show_error", "處理失敗", f"發生嚴重錯誤:\n{e}"))
        
        finally:
            self.ui_queue.put(("set_ui_state", True))
            self.ui_queue.put(("update_status", "準備就緒。"))
            self.processing_lock.release() # 確保鎖最終會被釋放

    def _progress_update_handler(self, current: int, total: int, path: Path):
        """由背景執行緒呼叫，將更新指令放入佇列。"""
        self.ui_queue.put(("update_progress", current, total))
        self.ui_queue.put(("update_status", f"正在處理 [{current}/{total}]: {path.name}"))
        
    def process_ui_queue(self):
        """由 UI 主執行緒定期呼叫，安全地執行 UI 更新。"""
        try:
            message = self.ui_queue.get_nowait()
            command, *args = message
            # 使用 getattr 安全地獲取 view 上的方法並呼叫
            method = getattr(self.view, command, None)
            if method and callable(method):
                method(*args)
        except queue.Empty:
            # 佇列是空的，什麼都不做
            pass