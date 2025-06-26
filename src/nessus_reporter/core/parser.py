# src/nessus_reporter/core/parser.py

from lxml import etree
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# 為了型別提示，我們從 config_manager 導入 FieldConfig
# 這確保了傳入的設定物件結構是正確的
from .config_manager import FieldConfig, ConfigurationManager, ConfigError

class ParsingError(Exception):
    """當解析過程中發生錯誤時引發的基礎類別。"""
    pass

class ConfigurableDataParser:
    """
    一個通用的、由設定檔驅動的 XML 解析器。
    它被設計用來高效地解析 Nessus v2 格式的 XML 檔案。
    這個類別本身不儲存狀態，其所有方法均為靜態方法。
    """

    @staticmethod
    def _parse_single_item(report_item: etree._Element, fields_config: List[FieldConfig]) -> Dict[str, Any]:
        """
        [優化] 將單一項目解析邏輯提取到此輔助方法中，增強可測試性與可讀性。
        它負責根據設定規則，從單一的 <ReportItem> 元素中提取所有資料。
        """
        row_data = {}
        # 遍歷設定檔中定義的每一個欄位規則
        for field in fields_config:
            display_name = field['displayName']
            context_node = None  # 用於 XPath 查詢的上下文節點

            # 根據設定檔中的 source_tag 決定 XPath 的起點
            if field['source_tag'] == 'ReportItem':
                context_node = report_item
            elif field['source_tag'] == 'ReportHost':
                # [優化] 增加對 getparent() 回傳 None 的穩健性檢查
                parent = report_item.getparent()
                if parent is not None and parent.tag == 'ReportHost':
                    context_node = parent

            value = None # 預設值為 None
            if context_node is not None:
                # 使用 lxml 的 xpath() 方法執行查詢
                results = context_node.xpath(field['path'])
                value = results[0] if results else None
                
                # --- 資料轉換 ---
                if 'mapping' in field and value is not None:
                    value = field['mapping'].get(str(value), value)
            
            row_data[display_name] = value
        
        return row_data

    @staticmethod
    def parse_file(file_path: Path, fields_config: List[FieldConfig]) -> pd.DataFrame:
        """
        [優化] 將此方法設為靜態方法，因為它不依賴任何實例狀態。
        解析單一的 .nessus XML 檔案，並根據提供的設定規則提取資料。

        Args:
            file_path (Path): 要解析的 .nessus 檔案的路徑。
            fields_config (List[FieldConfig]): 從 ConfigurationManager 獲取的所有欄位設定。

        Returns:
            pd.DataFrame: 一個包含所有提取和轉換後資料的 pandas DataFrame。

        Raises:
            ParsingError: 如果檔案不存在、不是有效的 XML 或在解析時發生其他錯誤。
        """
        if not file_path.is_file():
            raise ParsingError(f"檔案不存在: {file_path}")

        all_rows_data = []

        try:
            # --- 效能最佳化：使用 lxml 的 iterparse ---
            context = etree.iterparse(str(file_path), events=('end',), tag='ReportItem')

            for event, report_item in context:
                # 調用輔助方法來處理單一元素的解析
                row_data = ConfigurableDataParser._parse_single_item(report_item, fields_config)
                all_rows_data.append(row_data)

                # --- 記憶體管理：關鍵步驟 ---
                report_item.clear()
                while report_item.getprevious() is not None:
                    del report_item.getparent()[0]
            
            del context

        except etree.XMLSyntaxError as e:
            raise ParsingError(f"XML 語法錯誤於檔案 {file_path}: {e}") from e
        except Exception as e:
            raise ParsingError(f"解析檔案 {file_path} 時發生未預期的錯誤: {e}") from e
        
        if not all_rows_data:
            return pd.DataFrame()

        # 指定 columns 以確保 DataFrame 結構的一致性
        ordered_columns = [field['displayName'] for field in fields_config]
        df = pd.DataFrame(all_rows_data, columns=ordered_columns)
        
        return df