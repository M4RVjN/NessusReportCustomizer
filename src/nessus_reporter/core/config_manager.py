# src/nessus_reporter/core/config_manager.py

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict

# --- 自訂例外類別 ---
class ConfigError(Exception):
    """ 設定管理員相關錯誤的基礎類別 """
    pass

class ConfigNotFoundError(ConfigError):
    """ 當找不到設定檔時引發 """
    pass

class InvalidConfigError(ConfigError):
    """ 當設定檔格式或內容無效時引發 """
    pass

class DuplicateIdError(InvalidConfigError):
    """ 當設定檔中發現重複的 field ID 時引發 """
    pass

# --- 定義欄位結構 ---
class FieldConfig(TypedDict, total=False):
    id: str           # 必要
    displayName: str  # 必要
    path: str         # 必要
    source_tag: str   # 必要
    default: bool
    description: str
    mapping: Dict[str, str]

class ConfigurationManager:
    """
    負責讀取、驗證並提供對 `config.yaml` 存取介面之物件
    """

    def __init__(self, fields: List[FieldConfig]):
        """
        一個簡單、快速的初始化方法。
        它的唯一職責是接收已經被驗證過的資料，並設定好內部狀態。
        它不執行任何 I/O 或複雜的驗證。

        Args:
            fields (List[FieldConfig]): 一個已經被驗證過的欄位設定列表。
        """
        self._fields: List[FieldConfig] = fields
        
        # 根據傳入的 fields 列表，建立一個用於快速查詢的字典
        self._fields_by_id: Dict[str, FieldConfig] = {
            field['id']: field for field in fields
        }

    @classmethod
    def from_file(cls, config_path: str = 'config.yaml') -> 'ConfigurationManager':
        """
        [工廠方法] 從一個 YAML 檔案讀取、驗證並創建一個 ConfigurationManager 實例。
        這是建議用來創建此類別物件的標準方式。

        Args:
            config_path (str): `config.yaml` 檔案的路徑。

        Returns:
            ConfigurationManager: 一個初始化完成且有效的實例。

        Raises:
            ConfigNotFoundError: 如果設定檔路徑不存在或不是一個檔案。
            InvalidConfigError: 如果 YAML 語法錯誤或結構不符合要求。
            DuplicateIdError: 如果設定檔中存在重複的 field 'id'。
        """
        path = Path(config_path)

        # 1. 驗證檔案是否存在
        if not path.is_file():
            raise ConfigNotFoundError(f"設定檔不存在: {path}")

        # 2. 讀取並解析 YAML
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except (IOError, yaml.YAMLError) as e:
            raise InvalidConfigError(f"讀取或解析設定檔時發生錯誤: {e}") from e

        # 3. 驗證基本結構
        if not isinstance(config_data, dict) or 'fields' not in config_data:
            raise InvalidConfigError("設定檔必須是一個包含 'fields' 鍵的字典。")
        
        fields_list = config_data['fields']
        if not isinstance(fields_list, list) or not fields_list:
            raise InvalidConfigError("'fields' 鍵的值必須是一個非空的列表。")

        # 4. 逐一驗證每個 field 的結構
        validated_fields: List[FieldConfig] = []
        required_keys = {'id', 'displayName', 'path', 'source_tag'}
        seen_ids = set()

        for field in fields_list:
            if not isinstance(field, dict):
                raise InvalidConfigError(f"Field 項目必須是字典: {field}")

            missing_keys = required_keys - set(field.keys())
            if missing_keys:
                raise InvalidConfigError(f"Field '{field.get('id', 'N/A')}' 缺少必要鍵: {', '.join(missing_keys)}")

            field_id = field['id']
            if field_id in seen_ids:
                raise DuplicateIdError(f"設定檔中發現重複的 ID: '{field_id}'")
            
            seen_ids.add(field_id)
            validated_fields.append(field) # type: ignore

        # 5. 使用驗證過的資料，透過 `cls()` (即 ConfigurationManager) 創建並回傳實例
        return cls(validated_fields)

    # --- 公開介面 (Public Interface) ---

    def get_all_fields(self) -> List[FieldConfig]:
        """
        獲取所有已定義的欄位設定。
        """
        return self._fields.copy()

    def get_field_by_id(self, field_id: str) -> Optional[FieldConfig]:
        """
        根據欄位 ID 獲取特定的欄位設定。
        """
        field = self._fields_by_id.get(field_id)
        return field.copy() if field else None # type: ignore