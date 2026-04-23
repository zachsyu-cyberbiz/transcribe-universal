# Harness Reference
# 這份文件在 Onboarding 完成後讀取一次，以後不再重複讀取。
# 若需要查閱目錄結構或 JSON schema，重新 Read 此檔案。

---

## Layer 1：Output Management（檔案管理）

### 專案自動偵測

```
從當前工作目錄推斷專案名稱：
  ├─ 目錄路徑含已知專案名 → 使用該名稱
  ├─ 在 home 目錄或無法辨識 → 問使用者「這屬於哪個專案？」
  └─ 新專案 → 自動在 config.json 建立 mapping 並儲存
```

config.json 的 projects 欄位：
```json
{
  "projects": {
    "Elmer": "/Users/.../Biz/Elmer/transcripts/",
    "CYB": "/Users/.../CYB-Desktop/transcripts/"
  }
}
```

### 輸出目錄結構

```
{專案目錄}/transcripts/{YYYY-MM-DD}_{meeting-name}/
├── meeting-notes.md          ← 使用者編輯的版本
├── dispatch-analysis.md      ← Step 8c 後存入
├── drafts/                   ← Step 8d 各項行動草稿
│   ├── 02-line-to-elmer.md
│   └── 03-validation-agenda-internal.md
├── source/                   ← 來源檔案 symlink（不複製）
│   ├── part1.m4a → 原始路徑
│   └── photos/
│       └── IMG_001.jpg → 原始路徑
└── .raw/                     ← 機器生成，使用者不需手動操作
    ├── raw-transcript.md
    ├── meeting-notes-v0.md   ← Claude 原始版備份
    ├── ocr.txt
    ├── quality-check.json
    └── progress.json         ← 步驟進度追蹤（resume 用）
```

### 命名規則

- 目錄：`{YYYY-MM-DD}_{meeting-name-kebab-case}/`
- meeting-name 由使用者提供，或從音檔檔名推斷
- 特殊字元（macOS 冒號 `:`）→ 轉為絕對路徑

### progress.json（Resume 用）

每步驟完成時寫入，讓 session 中斷後可從斷點繼續：

```json
{
  "session_id": "2026-04-22_elmer",
  "last_completed_step": 4,
  "output_dir": "/path/to/transcripts/...",
  "audio_files": ["part1.m4a", "part2.m4a"],
  "meeting_type": "external",
  "participants": ["Zach", "Elmer"],
  "language": "zh"
}
```

Session 啟動時，如果發現 `.raw/progress.json` 且 `last_completed_step < 8`：
> 「上次的轉錄進行到 Step N，要繼續嗎？還是重新開始？」

---

## Layer 2：Transcript Index（轉錄追蹤）

**路徑：** `~/.transcribe-universal/transcript-index.json`

每次 Step 2 完成後追加一筆記錄：

```json
{
  "id": "2026-04-22_elmer-discussion",
  "date": "2026-04-22",
  "name": "和 Elmer 討論",
  "type": "external",
  "participants": ["Zach", "Elmer"],
  "project": "Elmer",
  "path": "/path/to/transcripts/...",
  "backend": "MLX Whisper",
  "duration_min": 89.6,
  "quality": {
    "hallucination_marks": 2,
    "simplified_chars_remaining": 0,
    "replacements_applied": 7
  },
  "dispatch": {
    "scanned": false,
    "action_items_total": null
  },
  "status": "transcribed"
}
```

Step 8c 完成後更新 `dispatch` 欄位。

**用途：**
- 同專案下次開會前，讀取上次未完成的 action items
- 追蹤長期品質趨勢（replacements 越來越少 = Whisper 越來越準）

---

## Layer 3：Session Context（下個 Session 的脈絡）

轉錄 + Dispatch 完成後，在專案 CLAUDE.md（若存在）底部追加：

```markdown
## 最近會議

- {日期} {會議名稱} → transcripts/{dir}/
  - 決定：[1-2 句]
  - 待辦：N 項（紅 X / 黃 Y / 綠 Z）
  - 分析報告：transcripts/{dir}/dispatch-analysis.md
```

規則：
- 只保留最近 5 筆，舊的自動移除
- 若專案目錄無 CLAUDE.md → 跳過，不建立

---

## Quality Harness（Step 5 完成後靜默跑）

| 檢查項目 | 通過標準 | 失敗時 |
|---------|---------|--------|
| 幻聽標記 `[⚠️ 音訊不清]` | ≤ 每 10 分鐘 2 次 | Step 6 加提醒 |
| 空白段落比例 | < 5% | Step 6 加提醒 |
| 簡體中文殘留 | 0 字 | Step 6 加提醒 + 建議安裝 opencc |
| Action Items 完整度 | 每項都有負責人 | Step 6 加提醒 |

沒問題 → 靜默，不在對話中顯示。
結果寫入 `.raw/quality-check.json` + `transcript-index.json`。

---

## Learning Loop（每次 /review-meeting-universal 後觸發）

| 層級 | 觸發條件 | 更新目標 | 記錄時機 |
|------|---------|---------|---------|
| Whisper 層 | 使用者改了拼音 / 人名 | `replacements.json` | 每次 |
| 結構化層 | 使用者改了格式 / 模板排序 | `preferences.json` | 首次發現重大偏好 |
| Dispatch 層 | 使用者選了 / 跳過哪些編號 | `dispatch-history.json` | 每次，>5 次後調整排序 |

所有學習資料存在 `~/.transcribe-universal/`，個人獨立，不影響其他使用者。
