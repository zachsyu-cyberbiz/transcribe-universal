# transcribe-universal — 安裝說明

版本：1.3.0 | 適用：Claude Code（Mac / Windows / Linux）

---

## 安裝步驟

> **推薦方式**：在 Claude Code 輸入 `/skill-adopt`，貼上 `https://github.com/zachsyu-cyberbiz/transcribe-universal` 自動安裝。

1. 把 `transcribe-universal/` 整個資料夾複製到 `~/.claude/skills/`
   ```bash
   cp -r transcribe-universal ~/.claude/skills/
   ```

2. 重啟 Claude Code（或在對話中輸入 `/reload`）

3. 輸入 `/transcribe-universal` → 自動觸發首次設定

---

## 首次設定（Onboarding）

Claude 會自動問你以下問題（不需要手動配置任何檔案）：

1. **語音辨識方式** — 本地（Mac 推薦）或 Groq（任何平台）
2. **中文轉換工具** — 若你用中文，會提示安裝 opencc（一行指令）

設定完成後直接開始使用，無需再設定。

---

## 需要的環境

| 需求 | Mac（Apple Silicon） | Mac（Intel）/ Windows / Linux |
|------|---------------------|-------------------------------|
| 語音辨識（本地） | `pip install mlx-whisper` | `pip install faster-whisper` |
| 語音辨識（雲端） | Groq API key（免費） | Groq API key（免費） |
| 中文繁簡轉換 | `pip install opencc-python-reimplemented` | 同左 |
| 圖片 OCR | macOS Vision（內建） | Tesseract（`brew install tesseract`） |
| 影片取幀 | `brew install ffmpeg` | 對應平台安裝 ffmpeg |
| Python | 3.9+ | 3.9+ |

---

## 重新設定 / 更換語音辨識方式

```
/transcribe-universal --setup
```

---

## 常見問題

**Q：說「語音辨識好像跑不起來」**
→ 確認 Python 版本 `python3 --version`，需要 3.9+
→ 若用 MLX：確認是 Apple Silicon Mac（M1/M2/M3/M4）

**Q：中文結果有簡體字**
→ 安裝 opencc：`pip install opencc-python-reimplemented`，然後重新執行

**Q：圖片 OCR 沒有文字 / 文字很少**
→ 這是正常的，Claude 會自動切換到 AI vision 分析圖片

**Q：多個錄音檔怎麼處理**
→ 在 Step 1 一起提供多個檔案路徑，系統會自動合併並對齊時間軸

---

## 檔案結構說明

```
transcribe-universal/
├── SKILL.md           ← Claude Code 讀取的核心指令（精簡版）
├── scripts/
│   ├── check-env.py        ← 環境偵測（Onboarding 時執行）
│   ├── transcribe-universal.py  ← 轉錄引擎
│   └── ocr-universal.py        ← 圖片 OCR
└── docs/              ← 參考文件（Claude 按需讀取，不常駐 context）
    ├── README.md      ← 本文件
    ├── templates.md   ← 4 種會議紀錄模板（Step 5 讀取）
    ├── channels.md    ← 9 種草稿管道規則（Step 8d 讀取）
    ├── harness.md     ← 檔案管理 + 追蹤系統說明（Onboarding 讀取）
    └── review.md      ← /review-meeting-universal 說明
```

---

## 版本記錄

| 版本 | 變更摘要 |
|------|---------|
| 1.3.0 | 拆分 docs/ 目錄；加入 progress.json（resume 功能）；加入 version 欄位；加入 guard conditions |
| 1.2.0 | 草稿存檔到 drafts/，自動開啟；LINE 草稿不含 Markdown 語法 |
| 1.1.0 | OpenCC 改為必要元件；check-env 詳細化；新增 Step O1.5 |
| 1.0.0 | 初始版本：MLX/Groq/faster-whisper + OCR + Intelligent Dispatch |
