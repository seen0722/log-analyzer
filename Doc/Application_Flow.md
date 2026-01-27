# AI Log Analyzer - 應用程式執行流程 (Application Flow)

本文件說明 `log-analyzer` 應用程式在後端實際運行的完整流程。當使用者上傳 ZIP 檔案並點擊 "Analyze" 時，系統會依序執行以下步驟：

## 1. 請求接收 (FastAPI Entry Point)
*   **檔案**: `main.py`
*   **Action**: 
    1.  接收前端 POST 請求 (`/analyze`)。
    2.  驗證 API Key (若無則使用 .env 預設值)。
    3.  建立唯一的 `session_id` (UUID)。
    4.  將上傳的 ZIP 檔案暫存至 `uploads/{session_id}/` 目錄。

## 2. 檔案解壓縮與分類 (Extraction)
*   **檔案**: `analyzer/extractor.py`
*   **Function**: `extract_zip_and_find_logs(zip_path, extract_to)`
*   **流程**:
    1.  解壓縮 ZIP 檔案。
    2.  遞迴掃描目錄，尋找關鍵日誌檔案：
        *   **Bugreport**: 檔名包含 `bugreport` 且結尾為 `.txt`。
        *   **ANR Traces**: 路徑包含 `anr` 或檔名包含 `traces`。
        *   **Logcat**: (選擇性) 檔名包含 `logcat`。
    3.  回傳一個包含各類日誌路徑的字典 `log_files`。

## 3. 日誌解析與關鍵字過濾 (Parsing)
*   **檔案**: `analyzer/parser.py`
*   **Function**: `parse_logs(log_files)`
*   **流程**:
    1.  **ANR 解析**:
        *   讀取 Trace 檔案標頭 (Subject)，找出 Blocked Thread。
        *   擷取該 Thread 的 Stack Trace (前 2000 字元)。
    2.  **Bugreport/Logcat 解析**:
        *   逐行讀取龐大的 Log 檔案。
        *   **關鍵字過濾 (Heuristics)**: 系統僅保留包含以下關鍵字的行及其後續 10-20 行 Context，以節省 Token 並聚焦問題：
            *   `FATAL EXCEPTION` (Crash)
            *   `ANR in` (ANR)
            *   `Watchdog` (系統卡死)
            *   `timed out` / `timeout` (新增: 抓取 HAL/Hardware 超時)
            *   `qcError` (新增: 抓取 Modem 錯誤)
            *   `Unable to handle kernel paging` (Kernel Panic)
    3.  將所有過濾後的證據組合成一個純文字字串 `log_evidence`。

## 4. AI 智能分析 (LLM Analysis)
*   **檔案**: `analyzer/llm.py`
*   **Function**: `analyze_with_llm(log_evidence, api_key, model)`
*   **流程**:
    1.  **System Prompt**: 設定 AI 人設為 "Senior Android BSP Technical Expert"，並強制規定輸出格式 (Markdown, Evidence 需引用 Source)。
    2.  **User Prompt**: 填入上一步解析出的 `log_evidence`。
    3.  **API Call**: 呼叫 OpenAI API (預設 `gpt-4o`)。
    4.  取得 AI 生成的 Markdown 格式 Root Cause Analysis (RCA) 報告。

## 5. 報告生成 (Report Generation)
*   **檔案**: `analyzer/report_generator.py`
*   **Function**: `generate_pdf_report(analysis_result, session_id, output_dir)`
*   **流程**:
    1.  **Markdown**: 將 AI 回傳的文字存為 `.md` 檔。
    2.  **HTML**: 
        *   使用 `markdown` 套件將內容轉為 HTML。
        *   **注入樣式**: 讀取 `static/report.css` (包含 Inter 字體、淺色代碼區塊樣式) 並嵌入 HTML Header。
        *   輸出完整的 `.html` 檔案。
    3.  **PDF**:
        *   呼叫系統安裝的 Google Chrome (Headless Mode)。
        *   指令: `chrome --headless --print-to-pdf=report.pdf report.html`。
    4.  回傳所有生成檔案的路徑給前端。

## 6. 前端展示 (Frontend Display)
*   **檔案**: `static/index.html`
*   **Action**: 
    1.  收到後端回應。
    2.  隱藏 Loading 動畫。
    3.  顯示 "Analysis Complete!" 及 PDF/HTML/Markdown 的下載連結。
