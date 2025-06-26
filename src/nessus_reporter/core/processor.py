# src/nessus_reporter/core/processor.py

import pandas as pd
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any

# 導入我們需要的兄弟模組和型別
from .config_manager import FieldConfig
from .parser import ConfigurableDataParser, ParsingError

# 定義回呼函式的型別簽名，以增強可讀性
ProgressCallback = Callable[[int, int, Path], None]

# [優化] 使用 Dataclass 來封裝回傳結果，使其更具可讀性和擴充性
@dataclass
class BatchProcessingResult:
    """存放批次處理結果的資料類別。"""
    dataframe: pd.DataFrame
    errors: List[Dict[str, Any]]

class BatchProcessor:
    """
    負責處理整個資料夾的批次任務。
    它會遍歷資料夾中的所有 .nessus 檔案，調用解析器，
    並將所有結果合併成一個單一的 DataFrame。
    """

    @staticmethod
    def process_folder(
        folder_path: Path, 
        fields_config: List[FieldConfig],
        progress_callback: Optional[ProgressCallback] = None
    ) -> BatchProcessingResult:
        """
        處理指定資料夾內的所有 .nessus 檔案。

        Args:
            folder_path (Path): 包含 .nessus 檔案的資料夾路徑。
            fields_config (List[FieldConfig]): 從 ConfigurationManager 獲取的欄位設定。
            progress_callback (Optional[ProgressCallback]): 
                一個可選的回呼函式，用於回報處理進度。

        Returns:
            BatchProcessingResult: 一個包含 dataframe 和 errors 兩個屬性的結果物件。
        """
        if not folder_path.is_dir():
            error = {"file": str(folder_path), "error": "提供的路徑不是一個有效的資料夾。"}
            return BatchProcessingResult(dataframe=pd.DataFrame(), errors=[error])

        nessus_files = list(folder_path.glob('*.nessus'))
        total_files = len(nessus_files)

        if total_files == 0:
            error = {"file": str(folder_path), "error": "資料夾中未找到任何 .nessus 檔案。"}
            return BatchProcessingResult(dataframe=pd.DataFrame(), errors=[error])

        dfs_to_merge: List[pd.DataFrame] = []
        parsing_errors: List[Dict[str, Any]] = []

        for i, file_path in enumerate(nessus_files):
            current_file_num = i + 1
            
            if progress_callback:
                progress_callback(current_file_num, total_files, file_path)

            try:
                parsed_df = ConfigurableDataParser.parse_file(file_path, fields_config)
                if not parsed_df.empty:
                    dfs_to_merge.append(parsed_df)
            
            except ParsingError as e:
                error_info = {"file": str(file_path), "error": str(e)}
                parsing_errors.append(error_info)
                # [優化] 引入日誌記錄。使用 warning 等級，因為這是一個被預期且已處理的錯誤。
                logging.warning(f"跳過檔案 (解析失敗): {file_path.name} | 原因: {e}")
        
        if not dfs_to_merge:
            return BatchProcessingResult(dataframe=pd.DataFrame(), errors=parsing_errors)

        # 理論上的效能瓶頸：如果所有 df 都很大，這裡會佔用較多記憶體。
        # 但對於絕大多數情況，這是最高效的作法。
        final_df = pd.concat(dfs_to_merge, ignore_index=True)
        
        return BatchProcessingResult(dataframe=final_df, errors=parsing_errors)


# --- 使用範例 (已更新以反映優化後的程式碼) ---
if __name__ == '__main__':
    # 設定日誌的基本組態，讓 logging.warning 的訊息能顯示在終端機
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 為了能直接執行此檔案，我們先手動處理一下路徑問題
    try:
        from config_manager import ConfigurationManager, ConfigError
    except ImportError:
        import sys
        src_path = str(Path(__file__).resolve().parents[2])
        if src_path not in sys.path:
            sys.path.append(src_path)
        from nessus_reporter.core.config_manager import ConfigurationManager, ConfigError
    
    def console_progress_reporter(current: int, total: int, path: Path):
        print(f"正在處理 [{current}/{total}]: {path.name}")

    try:
        print("正在載入設定檔...")
        config_manager = ConfigurationManager.from_file('config.yaml')
        fields_config = config_manager.get_all_fields()
        print("設定檔載入成功。")

        input_folder = Path('data/input')
        print(f"\n準備處理資料夾: {input_folder}")

        # 執行批次處理
        result = BatchProcessor.process_folder(
            input_folder, 
            fields_config, 
            progress_callback=console_progress_reporter
        )

        print("\n--- 批次處理完成 ---")

        # [優化] 使用 result.dataframe 和 result.errors 來存取結果
        if not result.dataframe.empty:
            print(f"\n成功合併 {len(result.dataframe)} 筆資料。")
            print("合併後的 DataFrame Info:")
            result.dataframe.info()
            print("\n合併後 DataFrame 的前 5 筆資料:")
            print(result.dataframe.head())
        
        if result.errors:
            print(f"\n處理過程中發生了 {len(result.errors)} 個錯誤:")
            for err in result.errors:
                print(f"  - 檔案: {err['file']}\n    錯誤訊息: {err['error']}")

    except ConfigError as e:
        print(f"[設定錯誤] {e}")
    except Exception as e:
        print(f"[未預期錯誤] {e}")