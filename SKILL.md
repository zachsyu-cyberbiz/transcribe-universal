---
name: transcribe-universal
version: "1.3.0"
description: 轉錄會議錄音並整理為會議紀錄，跨平台支援（Mac/Windows/Linux），自動識別後續工作項目。
user_invocable: true
---
# /transcribe-universal

轉錄錄音檔 → 整理會議紀錄 → 主動識別後續工作 → 協助起草 follow-up 內容。

## 腳本路徑（執行時直接用，不要讓使用者看到）

```
check-env   : ~/.claude/skills/transcribe-universal/scripts/check-env.py
transcribe  : ~/.claude/skills/transcribe-universal/scripts/transcribe-universal.py
ocr         : ~/.claude/skills/transcribe-universal/scripts/ocr-universal.py
config      : ~/.transcribe-universal/config.json
replacements: ~/.transcribe-universal/replacements.json
```

---

## 進入點

```
/transcribe-universal 執行時：
  ├─ 帶 --setup 參數            → Onboarding
  ├─ ~/.transcribe-universal/config.json 不存在 → Onboarding
  └─ config.json 存在           → 檢查 .raw/progress.json → Step 1 或 Resume
```

### Resume 邏輯

若當前目錄有 `.raw/progress.json` 且 `last_completed_step < 8`：

> 「上次的轉錄做到 Step {N}，要繼續嗎？還是重新開始？」

使用者選繼續 → 從 Step N+1 開始，使用 progress.json 裡的參數。

---

## Onboarding（首次使用 / --setup）

**O1 — 環境偵測**

```bash
python3 ~/.claude/skills/transcribe-universal/scripts/check-env.py
```

解析 JSON 輸出，用自然語言告訴使用者：

- 有 MLX 或 faster-whisper → 「你的電腦可以在本地跑語音辨識，速度快而且免費。要用這個方式嗎？」
- 沒有本地模型 → 「建議設定 Groq — 免費、速度快。需要一組金鑰，不知道怎麼取得的話：<https://app.guideflow.com/player/np18zw3fek，取得後把金鑰貼給我就好。」>

**O1.5 — 中文必備元件（僅限 zh / zh-tw）**

若 `opencc.available == false` 且語言為中文：

> 「有個小工具要裝一下，Whisper 有時候會輸出簡體字，這個會自動幫你轉繁體。」
> `pip install opencc-python-reimplemented` → 若使用者同意，直接執行。

這不是 optional。缺少 OpenCC 會導致轉錄結果混雜簡體字。

**O2 — 寫入設定**

```json
// 寫入 ~/.transcribe-universal/config.json
{
  "backend": "mlx | groq | faster_whisper | openai_whisper",
  "groq_api_key_env": "GROQ_API_KEY",
  "default_language": "zh",
  "replacements_path": "~/.transcribe-universal/replacements.json",
  "output_base": "./transcripts",
  "notifications": true
}
```

Groq 使用者 → 引導設定 `GROQ_API_KEY` 環境變數（shell profile 或 .env）。

**O3 — 建立糾錯字典（若不存在）**

```json
// 寫入 ~/.transcribe-universal/replacements.json
{ "_comment": "語音辨識常見錯誤修正。key=錯誤，value=正確。每次轉錄後自動累積。" }
```

**O4 — 確認完成 + 讀取 Harness 文件**

告訴使用者：「設定完成！以後直接執行 /transcribe-universal 就好，不用再設定。」

```
→ Read ~/.claude/skills/transcribe-universal/docs/harness.md
```

---

## 主流程

### Step 1 — 收集輸入

一次問完（不要分開問）：

> 「請提供以下資訊：
>
> 1. 錄音檔在哪？（把檔案拖進來，或告訴我路徑）
> 2. 有哪些人參加？（名字 + 角色，例如 "Nick — Canon 品牌經理"）
> 3. 這是什麼類型的會議？（內部 / 客戶 / 講座 / 高層）
> 4. 有沒有相關的關鍵詞？（公司名、產品名）
> 5. 有截圖或照片嗎？（optional）
> 6. 誰是主要發言者？」

使用者只丟了檔案路徑也接受 — 從已知資訊推斷，並確認。

完成後寫入 `.raw/progress.json`（`last_completed_step: 1`）。

---

### Step 2 — 轉錄

Guard：讀取 config.json，確認 backend 設定存在。

若 `.raw/raw-transcript.md` 已存在 → 詢問：「偵測到上次的轉錄記錄，要重新跑還是用現有的？」

```bash
# 單檔
python3 ~/.claude/skills/transcribe-universal/scripts/transcribe-universal.py \
  --file "錄音檔路徑" --name "會議名稱" --context "參與者,公司名,關鍵詞" --language "zh"

# 多檔（自動 merge + time_offset）
python3 ~/.claude/skills/transcribe-universal/scripts/transcribe-universal.py \
  --file "path1.m4a" "path2.m4a" --name "會議名稱" --context "..."
```

解析腳本最後一行 JSON 輸出，取得 `output_dir`、`elapsed_sec`、`segments`。
完成後更新 `progress.json`（`last_completed_step: 2`）。

---

### Step 3 — 名詞確認

Guard：確認 `{output_dir}/.raw/raw-transcript.md` 存在。

掃描可疑名詞（拼音相近、不在 replacements.json 的詞）。若有，一次列出：

> 「轉錄中有幾個不確定的名詞：
>
> - "Cannon" → 是 Canon 嗎？
> - "尼克" → 是 Nick 嗎？
>   確認後我會記住，下次不用再問。」

確認後 → 更新 `replacements.json` + 在 raw-transcript.md 中套用修正。
若無可疑名詞 → 靜默跳過。

---

### Step 4 — OCR（有截圖/照片才執行）

Guard：Step 1 有提供圖片路徑才執行。無圖片 → 跳過。

```bash
# 多張圖
python3 ~/.claude/skills/transcribe-universal/scripts/ocr-universal.py image1.jpg image2.jpg
# 整個目錄
python3 ~/.claude/skills/transcribe-universal/scripts/ocr-universal.py --dir slides/
```

若結果中 `needs_claude_vision: true`（文字 < 10 字元）→ 直接用 Claude vision 分析圖片。
OCR 結果存入 `{output_dir}/.raw/ocr.txt`。

---

### Step 5 — 結構化

Guard：確認 raw-transcript.md 存在。

```
→ Read ~/.claude/skills/transcribe-universal/docs/templates.md
```

根據 Step 1 的 `type` 選對應模板：

- `internal`  → internal 模板
- `external`  → external 模板
- `lecture`   → lecture 模板
- `executive` → executive 模板
- 不確定 → 問使用者

讀取 raw-transcript.md + ocr.txt，填入模板內容（結論式 bullet points，不要口語化逐字稿）。

生成：

- `{output_dir}/meeting-notes.md` — 使用者會編輯的版本
- `{output_dir}/.raw/meeting-notes-v0.md` — 備份，不要修改

**背景靜默跑 Quality Harness：**

- 幻聽標記 > 每 10 分鐘 2 次 → Step 6 加提醒
- 簡體字殘留 > 0 → Step 6 加提醒
- Action Items 缺負責人 → Step 6 加提醒
- 無問題 → 靜默
- 結果寫入 `.raw/quality-check.json`

---

### Step 6 — 開啟檔案 + Review 提示

```bash
# macOS
open "{output_dir}/meeting-notes.md"
# Windows
start "{output_dir}/meeting-notes.md"
# Linux
xdg-open "{output_dir}/meeting-notes.md"
```

顯示完成訊息：

> ✅ 轉錄完成！
> 🔧 使用：{backend}（{duration} 分鐘 → {elapsed} 秒）
> 📄 已開啟會議紀錄：{output_dir}/meeting-notes.md
>
> ⚠️ 請特別確認「誰說了什麼」的部分，轉錄可能有誤。
> 改完後存檔，回來跟我說「改好了」。

若 Quality Harness 有警告 → 在此加入一行提醒。

---

### Step 7 — 等待使用者 Review

等使用者說「改好了」「OK」「好了」或類似語意。
**在此之前不主動做任何事。**

---

### Step 8 — Intelligent Dispatch

Guard：確認 `{output_dir}/meeting-notes.md` 存在且使用者已確認 review 完成。

**8a — 8 維度深度掃描**（讀最新的 meeting-notes.md）

| # | 維度      | 識別目標                       |
| - | --------- | ------------------------------ |
| 1 | 決策已做  | 確認的結論、方向               |
| 2 | 決策未做  | 被擱置、需更多資訊             |
| 3 | 我方承諾  | 我方答應要做的事               |
| 4 | 對方承諾  | 對方答應要做的事               |
| 5 | 新資訊    | 首次出現的公司/產品/技術       |
| 6 | 風險/疑慮 | 法律、財務、合規               |
| 7 | 關係動態  | 態度轉變、政治考量（不寫書面） |
| 8 | 隱含需求  | 弦外之音、未說出的期望         |

**8b — 參與者角色判定**

推斷：內部成員 / 外部客戶 / 外部夥伴 / 決策層 / 法務 / 財務 / 工程師 / 以角色判定
也識別：未出席但被提及 → 需要同步資訊的利害關係人

**8c — 三層優先級清單**

掃描完成後，將結果存入 `{output_dir}/dispatch-analysis.md`，並在對話中顯示：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 會議分析完成 — 識別到 N 項後續行動
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 今天（X 項）
| ☐N | 行動 | 對象 | 管道 |

🟡 本週（Y 項）
...

🟢 之後（Z 項）
...

📎 敏感內容提醒：[若有]

💬 選好之後告訴我編號（如 "1,3,4"），
   我會把草稿存成檔案一份一份給你確認。
```

**8d — 並行起草**

```
→ Read ~/.claude/skills/transcribe-universal/docs/channels.md
```

使用者選好編號後，同時處理（parallel agents 若可用，否則依序）。

每完成一份：

1. 存入 `{output_dir}/drafts/{NN}-{channel}-{recipient}.md`
2. 自動開啟（open / start / xdg-open）
3. 對話告知：「✅ [N/M] 草稿已存至 drafts/NN-xxx.md，已開啟。要修改嗎？」

等使用者確認後再處理下一份。

---

## 錯誤處理

不顯示技術錯誤訊息。遇到問題：「好像遇到問題了，[一句話說明] + [建議做法]」

| 狀況             | 說法                                                                     |
| ---------------- | ------------------------------------------------------------------------ |
| 音檔無法讀取     | 「錄音檔好像開不了，可以確認是 .m4a 或 .mp3 嗎？」                       |
| 轉錄腳本無輸出   | 「語音辨識好像沒有跑起來，要我重試一次嗎？」                             |
| OCR 全部失敗     | 「圖片辨識遇到問題，我改用另一種方式分析。」→ fallback 到 Claude vision |
| 沒有網路（Groq） | 「好像連不上辨識服務，要改用本地方式嗎？」                               |

---

## UX 語言規則（全程適用）

禁止出現的詞 → 改用的說法：

- "backend" → "語音辨識方式"
- "API key" → "金鑰"
- "file path" → "把檔案拖進來，或告訴我在哪"
- "config.json / JSON / script" → 不提，背景靜默處理

語氣：像同事在旁邊帶你，不是在讀操作手冊。

---

## 安全閥（不可違反）

| 永遠做                                 | 永遠不做                    |
| -------------------------------------- | --------------------------- |
| ✅ 主動識別所有可能的 follow-up        | ❌ 自動發送任何外部通訊     |
| ✅ 提供完整清單讓使用者選擇            | ❌ 跳過確認直接執行         |
| ✅ 草稿存成檔案後自動開啟              | ❌ 一口氣把所有草稿全部輸出 |
| ✅ 標記敏感內容                        | ❌ 在非授權管道透露敏感資訊 |
| ✅ 轉錄完成後自動開啟 meeting-notes.md | ❌ 只印路徑讓使用者自己找   |
| ✅ Step 間保存 progress.json           | ❌ 中斷後重複執行已完成步驟 |
