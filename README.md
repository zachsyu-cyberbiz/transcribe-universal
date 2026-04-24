# transcribe-universal

一個 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill — 把錄音、截圖、筆記變成可行動的會議紀錄。

> 錄音檔、投影片截圖、手寫筆記通通拖進來 → 自動轉錄 + OCR → 整理成會議紀錄 → 識別後續工作 → 幫你起草 follow-up。

---

## 亮點

### 什麼都丟進來

不只是錄音。投影片截圖、白板照片、手寫筆記 — 全部拖進對話，自動辨識並整合到會議紀錄裡。多段錄音也沒問題，自動對齊時間軸合併。

### 零設定，開口就用

首次輸入 `/transcribe-universal`，系統自動偵測你的環境、引導你選擇語音辨識方式、幫你裝好需要的工具。不用碰任何設定檔，不用看任何技術文件。

### 4 種會議模板，自動套用

客戶會議、內部會議、講座筆記、高層簡報 — 根據會議類型自動選擇對應模板，產出包含 Executive Summary、Action Items、決策紀錄的結構化會議紀錄。

### 會後智慧分析

轉錄只是開始。系統會對會議內容做 8 個維度的深度掃描：

| 維度 | 識別什麼 |
|------|---------|
| 已做的決策 | 確認的結論、方向 |
| 未做的決策 | 被擱置、需要更多資訊的議題 |
| 我方承諾 | 我們答應要做的事 |
| 對方承諾 | 對方答應要做的事 |
| 新資訊 | 首次出現的公司、產品、技術 |
| 風險與疑慮 | 法律、財務、合規相關 |
| 關係動態 | 態度轉變、政治考量 |
| 隱含需求 | 弦外之音、未說出的期望 |

### 自動起草 follow-up，按優先級分層

分析完成後，依緊急程度整理成三層待辦清單：

- **今天** — 需要立即處理的事項
- **本週** — 這週內要完成的工作
- **之後** — 可以稍後處理的項目

你選好要處理哪幾項，系統就幫你起草對應的 follow-up，支援 9 種管道：

> Email（外部 / 法務）、LINE、Slack、Executive Brief、Calendar 邀約、任務指派、議程、研究備忘

每種管道有專屬格式 — LINE 草稿不會有 Markdown 語法，Email 自動偵測對方語言切換中英文，Executive Brief 只留決策者需要的資訊。

### 敏感內容自動把關

費用數字不會出現在 LINE 草稿裡、法律議題自動導向法務管道、其他客戶資訊不會外洩到不該出現的地方。你不用自己過濾，系統幫你守住。

### 永遠不會自動發送

所有草稿都是存成檔案、自動開啟讓你確認。系統不會代替你發送任何訊息。改好了再自己發，主導權在你手上。

### 越用越準

修正過的錯誤會自動記住，下次不會再犯。用得越多，轉錄品質越好。

### 更多特色

- **跨平台** — Mac（Apple Silicon / Intel）、Windows、Linux 全支援
- **4 種語音辨識引擎** — Groq（雲端免費，含註冊使用方式）、MLX Whisper、faster-whisper、OpenAI Whisper
- **中文優化** — Whisper 輸出簡體字？自動幫你轉繁體
- **斷點續傳** — 中斷可從上次進度繼續，不怕意外

---

## 使用情境

**開完客戶會議**
> 把錄音檔拖進來，附上投影片截圖。5 分鐘後拿到結構化的會議紀錄，確認內容後，系統幫你起草給客戶的 Email、給主管的 Executive Brief、給團隊的 Slack 摘要。

**內部週會**
> 多段錄音一起丟，自動合併。產出的紀錄已經標好每個人的 action items 和期限，直接分派就好。

**參加外部講座**
> 錄音 + 拍的投影片照片一起丟進來，產出完整的講座筆記，圖文對照。

---

## 使用流程

```
/transcribe-universal
```

```
Step 1  收集輸入    ← 錄音檔、截圖、筆記照片、參與者、會議類型
Step 2  轉錄        ← 自動選擇最佳引擎
Step 3  校正        ← 糾錯字典 + 繁簡轉換（背景執行）
Step 4  OCR         ← 辨識投影片截圖（如有提供）
Step 5  整理        ← 套用模板，產出會議紀錄
Step 6  檢視        ← 自動開啟紀錄供你確認
Step 7  修訂        ← 你修改，系統自動學習
Step 8  智慧派發    ← 8 維度分析 → 優先級清單 → 起草 follow-up
```

---

## 安裝

```bash
git clone https://github.com/zachsyu-cyberbiz/transcribe-universal.git ~/.claude/skills/transcribe-universal
```

安裝完成後，在 Claude Code 中輸入 `/transcribe-universal`，首次使用會自動引導你完成設定，不需要手動配置任何檔案。

### 更新

```bash
cd ~/.claude/skills/transcribe-universal && git pull
```

---

## 環境需求

- **Python 3.9+**
- **語音辨識引擎**（擇一，首次使用時會引導你選擇）：

| 引擎 | 平台 | 安裝方式 | 特點 |
|------|------|---------|------|
| MLX Whisper | Apple Silicon Mac | `pip install mlx-whisper` | 本地 GPU 加速，最快，免費 |
| Groq | 任何平台 | 免費申請 API key | 雲端處理，速度快，免費額度 |
| faster-whisper | 任何平台 | `pip install faster-whisper` | 本地 CPU/GPU |
| OpenAI Whisper | 任何平台 | `pip install openai-whisper` | 通用 fallback |

- **中文使用者**：`pip install opencc-python-reimplemented`（繁簡轉換，首次設定時會自動提示安裝）
- **影片取幀**：`ffmpeg`（`brew install ffmpeg` 或對應平台安裝方式）

---

## 使用方式

| 指令 | 說明 |
|------|------|
| `/transcribe-universal` | 開始轉錄（首次使用自動進入設定） |
| `/transcribe-universal --setup` | 重新設定（更換語音辨識引擎等） |
| `/review-meeting-universal` | 檢視並修訂已完成的會議紀錄 |

---

## 檔案結構

```
transcribe-universal/
├── SKILL.md                         # Claude Code skill 定義
├── scripts/
│   ├── transcribe-universal.py      # 轉錄引擎
│   ├── check-env.py                 # 環境偵測
│   └── ocr-universal.py            # 跨平台 OCR
└── docs/
    ├── README.md                    # 詳細技術文件
    ├── templates.md                 # 4 種會議紀錄模板
    ├── channels.md                  # 9 種 follow-up 管道規則
    ├── harness.md                   # 檔案管理 + 追蹤系統
    └── review.md                    # /review-meeting-universal 說明
```

---

## 版本記錄

| 版本 | 變更摘要 |
|------|---------|
| 1.4.0 | Groq 加入 exponential backoff retry；所有 backend 失敗時提供互動式復原選項 |
| 1.3.0 | 拆分 docs/ 目錄；加入斷點續傳（resume）功能；加入 guard conditions |
| 1.2.0 | 草稿存檔到 drafts/；自動開啟紀錄；LINE 草稿自動去除 Markdown 語法 |
| 1.1.0 | OpenCC 改為必要元件；環境偵測詳細化 |
| 1.0.0 | 初始版本：MLX / Groq / faster-whisper + OCR + Intelligent Dispatch |

---

## License

MIT
