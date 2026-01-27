# Root Cause Analysis (RCA): Keypad Unresponsive & System ANR

## 1. 問題摘要 (Executive Summary)
使用者喚醒裝置 (DVT3 Thorpe, OS-02.01.01.260119) 時，發生 **System Server ANR** (Application Not Responding)，導致按鍵無反應 (Keypad stopped working) 及無法截圖。系統稍後自動恢復。

經過 Log 分析，確認根本原因 (Root Cause) 為 **GNSS HAL 卡死** 導致 `system_server` 的關鍵執行緒 (`android.fg`) 堵塞，進而卡住了螢幕喚醒流程。

## 2. 根本原因 (Root Cause)
**GNSS HAL (GPS) 在進行 QMI 通訊時發生逾時 (Timeout)，導致 `system_server` 內的 `android.fg` 執行緒被長時間卡住。**

1.  **GNSS HAL Timeout**: 在 15:31:26 左右，GNSS Service 試圖透過 QMI 介面停止定位 session (`LOC_STOP`) 和設定運作模式 (`LOC_SET_OPERATION_MODE`)。
2.  **QMI 無回應**: 底層 Modem 或 QMI 介面無回應。經過 25 秒後 (15:31:51)，出現 `Function timed out` 和 `qcError 110` 錯誤。
3.  **System Server 堵塞**: `system_server` 的 `android.fg` 執行緒 (TID 1755) 此時正呼叫 `GnssHal::stop()` 並等待回應。由於 HAL 層卡住，導致此執行緒一直處於 `UNINTERRUPTIBLE_SLEEP` 或等待鎖定的狀態 (> 15秒)。
4.  **ANR 觸發**: 當使用者嘗試喚醒螢幕時，系統廣播 `android.intent.action.SCREEN_ON`。此廣播由 `android.fg` 執行緒負責派發。因為該執行緒已卡死在 GNSS HAL，導致廣播無法處理，最終觸發 Watchdog ANR。

## 3. 證據 (Evidence)

### ANR 資訊
- **時間**: `01-27 15:32:09.418`
- **進程**: `system_server` (PID 1702)
- **原因**: `Broadcast of Intent { act=android.intent.action.SCREEN_ON ... }`
- **卡住的執行緒**: `android.fg` (TID 1755)

### Stack Trace (android.fg)
該執行緒卡在 `android::hardware::gnss::V1_0::BpHwGnss::_hidl_stop` 等待回傳：
> **Source**: `FS/data/anr/anr_2026-01-27-15-32-09-441` (Lines 443-463)

```text
"android.fg" sysTid=1755
  #00 pc 00000000000c12ec  /apex/com.android.runtime/lib64/bionic/libc.so (__ioctl+12)
  ...
  #06 pc 00000000000a5ec8  /system/lib64/android.hardware.gnss@1.0.so (android::hardware::gnss::V1_0::BpHwGnss::_hidl_stop...+260)
  #07 pc 0000000000033d50  /system/lib64/libservices.core-gnss.so (android::gnss::GnssHal::stop()+160)
  ...
  #16 pc 0000000000256af0  /system/framework/services.jar (com.android.server.location.gnss.GnssLocationProvider.stopNavigating+44)
```

### GNSS HAL Error Logs (Logcat)
系統嘗試停止 GPS 時發生 Timeout：
> **Source**: `bugreport-T70-AQ3A.250408.001-2026-01-27-15-33-02.txt`

```text
(Line 22444) 01-27 15:31:26.891 ... I SWIGNSS : Stop:
(Line 22447) 01-27 15:31:26.891 ... D SWIGNSS : -> ... Send 11 bytes ...
... (25秒無回應) ...
(Line 22668) 01-27 15:31:51.818 ... W SWIGNSS : Function timed out
(Line 22670) 01-27 15:31:51.818 ... E SWIGNSS : swigps_setPosMode: Stop failed, qcError 110
```

## 4. 影響分析 (Impact Analysis)
- **為何 Keypad 失效？**: 按鍵事件 (Key events) 雖然由 InputDispatcher 接收，但需要上層 WindowManager Service (WMS) 和 PowerManager Service (PMS) 處理喚醒邏輯。這些關鍵服務依賴 `android.fg` 執行緒。當該執行緒卡死，系統無法完成 "從睡眠中喚醒" 的狀態轉換，導致對使用者輸入無反應。
- **為何無法截圖？**: 截圖功能同樣依賴 `system_server` 處理按鍵組合及畫面捕捉通知，因為核心服務卡死而無法執行。

## 5. 建議 (Recommendations)
1.  **檢查 Modem/GNSS 狀態**: 需由 Modem 團隊分析 QMI log (如果有的話) 或 Modem dump，確認為何 QMI 在 15:31:26 左右對 `LOC_STOP` 指令無回應。可能是 Modem 處於錯誤狀態或深眠導致喚醒失敗。
2.  **HAL 層防護**: 建議即使底層 Timeout，HAL 層應儘快回傳錯誤給 System Server，避免長時間 (超過 10-20秒) 阻塞主執行緒 (`android.fg`)，以防止整機 ANR。
