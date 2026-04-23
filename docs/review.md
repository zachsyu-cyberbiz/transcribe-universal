# /review-meeting-universal
# 在使用者執行 /review-meeting-universal 時讀取此檔案。

使用者 review 完 meeting-notes.md 後可單獨執行。
若 Intelligent Dispatch 已在 /transcribe-universal Step 8 跑過，此 skill 執行增量更新。

---

## 執行前 Guard

```
確認以下檔案存在：
  ├─ {output_dir}/meeting-notes.md       ✅ 使用者編輯版
  ├─ {output_dir}/.raw/meeting-notes-v0.md  ✅ Claude 原始版
  └─ {output_dir}/.raw/raw-transcript.md ✅ 原始逐字稿
若缺少任何一個 → 告知使用者，詢問是否要補跑對應步驟。
```

---

## Phase A：品質 Review

1. 讀取並 diff `meeting-notes.md` vs `.raw/meeting-notes-v0.md`
2. 分三類處理差異：

| 差異類型 | 判斷方式 | 處理 |
|---------|---------|------|
| Whisper 錯誤（拼音、人名） | 使用者改了一個詞，不是整段重寫 | 更新 `replacements.json`，下次自動套用 |
| 結構化判斷錯誤（speaker、段落） | 整段被移動或刪除 | 記入改善建議，不自動改 |
| 風格偏好（格式、用詞） | 同類改動出現 ≥2 次 | 更新 `preferences.json`（只記重大偏好） |

3. 印出 Checkpoint 報告：

```
✅ Quality Review 完成
  - Whisper 修正：N 個詞 → 已更新到糾錯字典
  - 結構改動：N 處 → 下次生成時參考
  - 風格偏好：[記錄到的偏好描述，若有]
```

---

## Phase B：增量 Dispatch 更新

```
檢查 dispatch-analysis.md 是否存在：
  ├─ 存在（Step 8 已跑過）→ 執行增量更新（見下）
  └─ 不存在（使用者跳過 Step 8）→ 執行完整 8 維度掃描
```

### 增量更新規則

| 使用者在 meeting-notes 做了什麼 | 對應 dispatch 更新 |
|-----------------------------|-------------------|
| 新增 Action Item | 追加到清單（標記為 A新） |
| 刪除某段討論 | 對應草稿項目標記為「已取消」 |
| 修改人名 / 歸屬 | 更新 dispatch 對象欄位 |
| 修改期限 | 更新對應 Action Item 期限 |

印出差異摘要後，詢問：
> 「要繼續處理剩下的 N 個項目嗎？還是有新的需要補充？」
