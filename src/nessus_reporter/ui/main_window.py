# src/nessus_reporter/ui/main_window.py

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional, Dict
import sys  # resource_path 導入 sys

def resource_path(relative_path: str) -> Path:
    """
    獲取資源檔案的絕對路徑。
    在開發環境和 PyInstaller 打包後的環境中都能正常運作。
    """
    try:
        # PyInstaller 建立一個臨時資料夾，並將路徑儲存在 _MEIPASS 中
        base_path = Path(sys._MEIPASS)
    except Exception:
        # 開發環境中，sys._MEIPASS 不存在，我們會使用目前的檔案路徑
        base_path = Path(".").resolve()
    
    return base_path / relative_path

# 導入我們的抽象基礎類別和控制器
from ..app_controller import AppController, IView

class MainWindow(ctk.CTk, IView):
    """
    應用程式的主視窗。
    它實現了 IView 介面，負責所有視覺呈現和使用者互動的捕捉。
    """
    def __init__(self, controller: AppController):
        super().__init__()

        self.controller = controller

        # --- 視窗基本設定 ---
        self.title("Nessus 報告客製化工具")

        try:
            icon_path = resource_path("resources/icons/IE.ico")
            self.iconbitmap(icon_path)
        except Exception as e:
            # 如果圖示載入失敗，只在終端機印出警告，不讓程式崩潰
            print(f"警告：無法載入圖示檔案 {icon_path}。錯誤: {e}")

        self.geometry("600x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # 允許滾動區域擴展

        # --- 內部狀態變數 ---
        self.input_folder_path: Optional[Path] = None
        self.checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.checkbox_vars: Dict[str, ctk.BooleanVar] = {}

        # --- 建立並佈局所有 UI 元件 ---
        self._create_widgets()
        self._populate_fields_from_config()
        
        # --- 啟動 UI 佇列輪詢 ---
        self.after(100, self._process_ui_queue)

    def _create_widgets(self):
        """私有方法，建立所有靜態 UI 元件。"""
        # --- 上方區域：資料夾選擇 ---
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        self.select_folder_button = ctk.CTkButton(top_frame, text="選擇來源資料夾", command=self._on_select_folder_click)
        self.select_folder_button.grid(row=0, column=0, padx=10, pady=10)

        self.folder_path_label = ctk.CTkLabel(top_frame, text="尚未選擇資料夾", anchor="w")
        self.folder_path_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # --- 中間區域：動態欄位選擇 ---
        ctk.CTkLabel(self, text="請選擇要匯出的欄位:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # --- 底部區域：執行與狀態回報 ---
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.generate_button = ctk.CTkButton(bottom_frame, text="生成 Excel 報告", command=self._on_generate_report_click, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.generate_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(bottom_frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")

        self.status_label = ctk.CTkLabel(bottom_frame, text="準備就緒", anchor="w")
        self.status_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")

    def _populate_fields_from_config(self):
        """
        [動態生成] 根據從控制器獲取的設定檔，動態建立所有核取方塊。
        """
        fields = self.controller.fields_config
        for i, field in enumerate(fields):
            display_name = field['displayName']
            var = ctk.BooleanVar()
            # 根據設定檔中的 'default' 值來設定核取方塊的預設狀態
            var.set(field.get('default', False))
            
            checkbox = ctk.CTkCheckBox(
                self.scrollable_frame, 
                text=display_name,
                variable=var
            )
            checkbox.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            # 將變數儲存起來，以便後續獲取其狀態
            self.checkbox_vars[display_name] = var

    def _process_ui_queue(self):
        """
        UI 主迴圈的一部分，定期檢查並處理來自控制器的 UI 更新指令。
        """
        self.controller.process_ui_queue()
        # 安排在 100 毫秒後再次執行自己，形成一個輪詢迴圈
        self.after(100, self._process_ui_queue)

    # --- UI 事件處理函式 ---
    def _on_select_folder_click(self):
        """處理「選擇資料夾」按鈕的點擊事件。"""
        # 使用 tkinter 內建的檔案對話框
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.input_folder_path = Path(folder_selected)
            self.folder_path_label.configure(text=str(self.input_folder_path))
            self.update_status(f"已選擇資料夾: {self.input_folder_path.name}")

    def _on_generate_report_click(self):
        """處理「生成報告」按鈕的點擊事件，將請求轉發給控制器。"""
        self.controller.start_processing()

    # --- IView 介面方法的具體實作 ---

    def show_error(self, title: str, message: str):
        messagebox.showerror(title, message, parent=self)

    def show_info(self, title: str, message: str):
        messagebox.showinfo(title, message, parent=self)

    def update_status(self, text: str):
        self.status_label.configure(text=text)

    def update_progress(self, current: int, total: int):
        progress_value = float(current) / float(total)
        self.progress_bar.set(progress_value)

    def set_ui_state(self, is_enabled: bool):
        state = "normal" if is_enabled else "disabled"
        self.generate_button.configure(state=state)
        self.select_folder_button.configure(state=state)

    def get_selected_columns(self) -> List[str]:
        return [name for name, var in self.checkbox_vars.items() if var.get()]

    def ask_for_input_folder(self) -> Optional[Path]:
        # 這個方法現在直接回傳使用者已經選擇的路徑
        return self.input_folder_path

    def ask_for_output_path(self) -> Optional[Path]:
        # 彈出「另存新檔」對話框
        file_path = filedialog.asksaveasfilename(
            title="儲存 Excel 報告",
            defaultextension=".xlsx",
            filetypes=[("Excel 活頁簿", "*.xlsx"), ("所有檔案", "*.*")]
        )
        return Path(file_path) if file_path else None
