# transcribe-universal

一個 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill — 把錄音變成可行動的會議紀錄。

> 錄音檔拖進來 → 自動轉錄 → 整理成會議紀錄 → 識別後續工作 → 幫你起草 follow-up。

---

## 亮點

| | 特色 | 說明 |
|---|---|---|
| **一鍵轉錄** | 拖入錄音檔，自動產出完整會議紀錄 | 支援 `.m4a`、`.mp3` 及所有 ffmpeg 支援的音訊 / 影片格式 |
| **跨平台** | Mac / Windows / Linux 全支援 | Apple Silicon 有專屬加速（MLX Whisper） |
| **多引擎** | 4 種語音辨識引擎自由選擇 | MLX Whisper（本地免費最快）、Groq（雲端免費）、faster-whisper、OpenAI Whisper |
| **智慧後續處理** | 自動識別 action items 並起草 follow-up | 支援 Email、LINE、Slack 等 9 種管道，按優先級分層 |
| **中文優化** | 自動繁簡轉換 + 中文語境校正 | Whisper 輸出簡體字？自動幫你轉繁體 |
| **圖片 OCR** | 投影片截圖自動辨識並嵌入紀錄 | macOS Vision / Windows OCR / Tesseract / Claude Vision 跨平台支援 |
| **越用越準** | 糾錯字典隨使用自動累積 | 修正過的錯誤下次不會再犯，學習你的用語習慣 |
| **斷點續傳** | 中斷可從上次進度繼續 | 不怕意外中斷，進度自動保存 |

---

## 使用流程

```
/transcribe-universal
```

```
Step 1  收集輸入    ← 錄音檔、參與者、會議類型
Step 2  轉錄        ← 自動選擇最佳引擎
Step 3  校正        ← 糾錯字典 + 繁簡轉換（背景執行）
Step 4  OCR         ← 辨識投影片截圖（如有提供）
Step 5  整理        ← 套用模板，產出會議紀錄
Step 6  檢視        ← 自動開啟紀錄供你確認
Step 7  修訂        ← 你修改，系統自動學習
Step 8  智慧派發    ← 分析決策 / 承諾 / 風險 → 起草 follow-up
```

---

## 安裝

```bash
git clone https://github.com/zachsyu-cyberbiz/transcribe-universal.git ~/.claude/skills/transcribe-universal
```

安裝完成後，在 Claude Code 中輸入 `/transcribe-universal`，首次使用會自動引導你完成設定（選擇語音辨識方式、安裝必要工具），不需要手動配置任何檔案。

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
