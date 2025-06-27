# src/nessus_reporter/core/parser.py

from lxml import etree
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Iterator
import itertools

# 導入我們需要的型別和錯誤類別
from .config_manager import FieldConfig, ConfigError

class ParsingError(Exception):
    """當解析過程中發生錯誤時引發的基礎類別。"""
    pass

class ConfigurableDataParser:
    """
    一個通用的、由設定檔驅動的 XML 解析器。
    此版本採用生成器模式，以實現最高的記憶體效率和程式碼清晰度。
    """

    @staticmethod
    def _extract_data(node: etree._Element, fields: List[FieldConfig]) -> Dict[str, Any]:
        """一個私有的輔助方法，根據提供的規則從指定的 XML 節點中提取資料。"""
        data = {}
        for field in fields:
            display_name = field['displayName']
            results = node.xpath(field['path'])
            value = results[0] if results else None
            
            if 'mapping' in field and value is not None:
                value = field['mapping'].get(str(value), value)
            
            data[display_name] = value
        return data

    @staticmethod
    def _iter_parsed_rows(file_path: Path, host_fields: List[FieldConfig], item_fields: List[FieldConfig]) -> Iterator[Dict[str, Any]]:
        """
        [優化] 這是一個生成器函式。
        它負責迭代解析 XML，並逐一 `yield` (產出) 處理好的單筆資料。
        """
        current_host_ip: str | None = None
        current_host_data: Dict[str, Any] = {}

        context = etree.iterparse(str(file_path), events=('end',), tag='ReportItem')

        for event, report_item in context:
            try:
                host_node = report_item.getparent()
                if host_node is None or host_node.tag != 'ReportHost':
                    continue

                ip = host_node.get('name')

                if ip != current_host_ip:
                    current_host_ip = ip
                    current_host_data = ConfigurableDataParser._extract_data(host_node, host_fields)

                item_data = ConfigurableDataParser._extract_data(report_item, item_fields)
                
                # 使用 yield 產出一筆合併後的完整資料
                yield {**current_host_data, **item_data}
            
            finally:
                # 記憶體清理是必須的，無論是否發生錯誤
                report_item.clear()
                while report_item.getprevious() is not None:
                    del report_item.getparent()[0]
        
        del context

    @staticmethod
    def parse_file(file_path: Path, fields_config: List[FieldConfig]) -> pd.DataFrame:
        """
        解析單一的 .nessus XML 檔案。
        此版本透過呼叫一個生成器來獲取資料流，並直接交給 pandas 處理。
        """
        if not file_path.is_file():
            raise ParsingError(f"檔案不存在: {file_path}")

        host_fields = [f for f in fields_config if f['source_tag'] == 'ReportHost']
        item_fields = [f for f in fields_config if f['source_tag'] == 'ReportItem']
        
        try:
            # 獲取資料流（生成器）
            row_iterator = ConfigurableDataParser._iter_parsed_rows(file_path, host_fields, item_fields)

            # --- 直接從迭代器建立 DataFrame ---
            # 這種方式比先建立一個巨大的 list 更節省記憶體
            df = pd.DataFrame(row_iterator)

            # 如果 df 是空的，直接回傳
            if df.empty:
                return df

            # 確保 DataFrame 的欄位順序與設定檔中定義的順序一致
            ordered_columns = [field['displayName'] for field in fields_config]
            # 過濾掉那些可能不存在於 df 中的欄位（例如，檔案中完全沒有出現的 optional 欄位）
            final_ordered_columns = [col for col in ordered_columns if col in df.columns]
            
            return df[final_ordered_columns]

        except etree.XMLSyntaxError as e:
            raise ParsingError(f"XML 語法錯誤於檔案 {file_path}: {e}") from e
        except Exception as e:
            raise ParsingError(f"解析檔案 {file_path} 時發生未預期的錯誤: {e}") from e
