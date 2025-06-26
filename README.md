# Nessus 報告客製化系統 (Nessus Report Customizer)

![版本](https://img.shields.io/badge/version-1.0.0-blue)
![Python 版本](https://img.shields.io/badge/python-3.8+-brightgreen)
![授權](https://img.shields.io/badge/license-MIT-lightgrey)
![建置狀態](https://img.shields.io/badge/build-passing-success)

一個強大且易於使用的桌面應用程式，旨在將繁瑣的 Nessus XML 弱點報告，快速轉換為格式精美、內容客製化的 Excel 檔案。專為提升資安分析師與專案管理人員的工作效率而設計。

![應用程式示意圖](https://placehold.co/800x450/cde4ff/6699ff?text=Application%20Screenshot)

---

## **目錄**

* [**1. 專案概述**](#1-專案概述)
* [**2. 功能特色**](#2-功能特色)
* [**3. 安裝指南**](#3-安裝指南)
* [**4. 使用範例**](#4-使用範例)
* [**5. 組態選項**](#5-組態選項)
* [**6. 貢獻指南**](#6-貢獻指南)
* [**7. 疑難排解**](#7-疑難排解)
* [**8. 常見問題 (FAQ)**](#8-常見問題-faq)
* [**9. 授權資訊**](#9-授權資訊)

---

## **1. 專案概述**

本專案的核心目標是將 Nessus 弱點掃描報告的處理流程自動化。透過一個直觀的圖形化介面，使用者可以批次處理多份 `.nessus` 報告，並根據一個外部設定檔 (`config.yaml`) 動態選擇所需欄位，最終生成一份可立即用於匯報或分析的 Excel 報告。

專案採用了現代化的軟體架構（MVC/MVP），透過多執行緒處理確保介面流暢，並利用設定檔驅動的設計實現了高度的可擴充性。

## **2. 功能特色**

* **圖形化使用者介面 (GUI)**: 基於 `CustomTkinter` 跨平台的介面。
* **批次處理**: 支援一次性處理整個資料夾的報告，大幅提升效率。
* **動態欄位選擇**: 透過 UI 上的核取方塊，自由組合您需要的報告欄位。
* **高度客製化**: 系統的解析規則完全由外部 `config.yaml` 檔案定義，無需修改程式碼即可擴充。
* **專業級 Excel 輸出**: 自動調整欄寬、凍結首行、內建篩選器，報告開箱即用。
* **非阻塞式處理**: 將耗時的檔案處理任務放到背景執行緒，確保 UI 不會卡頓。
* **穩健的錯誤處理**: 能優雅地處理空資料夾、損毀的 XML 檔案等異常情況。

---

## **3. 安裝指南**

**目標受眾：** 最終使用者、開發人員

### **先決條件**

* Python 3.8 或更高版本
* `pip` 套件管理器

### **安裝步驟**

1.  **複製本倉庫**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```

2.  **建立並啟動虛擬環境 (強烈建議)**
    ```bash
    # 建立虛擬環境
    python -m venv .venv

    # 啟動虛擬環境 (Windows)
    .\.venv\Scripts\activate

    # 啟動虛擬環境 (macOS/Linux)
    source .venv/bin/activate
    ```
    **常見陷阱：** 請確保您的終端機已成功進入虛擬環境（通常命令提示字元前會出現 `(.venv)` 字樣），以避免套件版本衝突。

3.  **安裝依賴套件**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(可選，供開發者使用) 安裝可編輯模式**
    這將讓您對原始碼的修改立即生效，並解決所有導入路徑問題。
    ```bash
    pip install -e .
    ```

---

## **4. 使用範例**

**目標受眾：** 最終使用者

1.  **執行程式**
    在專案根目錄下，執行主程式：
    ```bash
    python main.py
    ```
2.  **選擇來源資料夾**
    點擊「📁 選擇資料夾」按鈕，並選擇一個存放了您的 `.nessus` 檔案的資料夾。

3.  **勾選所需欄位**
    在中間的滾動區域，勾選所有您希望出現在 Excel 報告中的欄位。

4.  **生成報告**
    點擊「🚀 一鍵生成 Excel 報告！」按鈕，選擇報告的儲存位置和檔名。

5.  **完成**
    下方的進度條將顯示處理進度。完成後，程式會彈出成功提示視窗。

---

## **5. 組態選項**

**目標受眾：** 進階使用者、開發人員

本系統的核心是 `config.yaml`，它定義了所有可選欄位的解析規則。

### `config.yaml` 結構詳解

每個欄位都是一個包含以下鍵的物件：

| 鍵 (Key)      | 型別      | 是否必要 | 說明                                                              |
| :------------ | :-------- | :------- | :---------------------------------------------------------------- |
| `id`          | `string`  | **是** | 欄位的唯一內部識別碼，必須是英文且不重複。                         |
| `displayName` | `string`  | **是** | 顯示在 UI 和 Excel 標頭上的名稱。                                 |
| `path`        | `string`  | **是** | 用於提取資料的 XPath 路徑。`@` 表示屬性，`/text()` 表示文字。     |
| `source_tag`  | `string`  | **是** | XPath 的查詢起點，通常是 `ReportItem` 或 `ReportHost`。           |
| `default`     | `boolean` | 否       | 若為 `true`，此欄位在 UI 啟動時會預設被勾選。                     |
| `mapping`     | `object`  | 否       | 一個鍵值對應表，用於將原始值（如數字 `4`）轉換為文字（如 `Critical`）。 |

---

## **6. 貢獻指南**

**目標受眾：** 開發人員

我們非常歡迎各種形式的貢獻！無論是回報問題、提出建議，還是提交程式碼。

### **回報問題 (Bug Reports)**
如果您發現了任何問題，請在 GitHub 的 "Issues" 頁面中建立一個新的 issue，並請盡可能提供以下資訊：
* 您的作業系統與 Python 版本。
* 重現問題的詳細步驟。
* 相關的錯誤訊息或截圖。

### **提交程式碼 (Pull Requests)**
1.  **Fork** 本倉庫。
2.  建立一個新的分支 (`git checkout -b feature/AmazingFeature`)。
3.  進行您的修改。
4.  提交您的變更 (`git commit -m 'Add some AmazingFeature'`)。
5.  將分支推送到您的倉庫 (`git push origin feature/AmazingFeature`)。
6.  開啟一個 **Pull Request**。

**最佳實踐：** 在提交 Pull Request 前，請確保您的程式碼遵循專案現有的風格，並已通過所有測試（如果專案包含測試的話）。

---

## **7. 疑難排解**

* **問題：`ImportError` 或 `ModuleNotFoundError`**
    * **解決方案：** 確保您已啟動虛擬環境，並且是從**專案根目錄**執行程式。執行 `pip install -e .` 可以一勞永逸地解決此問題。

* **問題：`ConfigNotFoundError`**
    * **解決方案：** 確認 `config.yaml` 檔案確實存在於您執行程式的目錄（專案根目錄），並檢查檔名是否拼寫正確。

* **問題：`PermissionError: [Errno 13] Permission denied`**
    * **解決方案：** 您要儲存的目標 Excel 檔案目前正被其他程式（如 Microsoft Excel）打開。請關閉對應的 Excel 檔案後再試。

---

## **8. 常見問題 (FAQ)**

* **Q: 我可以新增一個需要用正則表達式處理的欄位嗎？**
    * **A:** 不建議直接在 `config.yaml` 中實現。最佳實踐是在 `AppController` 中進行「後處理」：先用 `config.yaml` 提取原始文字塊，然後在 `_run_batch_task` 方法中，對 `BatchProcessor` 回傳的 DataFrame 使用 Pandas 的 `.apply()` 方法和您的正則表達式函式來建立一個新欄位。

* **Q: 這個工具支援其他掃描器的報告嗎？**
    * **A:** 目前不支援。但由於採用了設定檔驅動的通用解析器，未來可以透過提供對應的 `config.yaml` 和微調 `Parser` 來擴充支援。

---

## **9. 授權資訊**

本專案採用 **MIT License** 授權。詳情請見 `LICENSE` 檔案。