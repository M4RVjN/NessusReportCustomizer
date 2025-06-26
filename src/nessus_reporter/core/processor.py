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
