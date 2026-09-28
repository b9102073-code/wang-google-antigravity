# Anti-Gravity 懶人包 #09：服務連接與工作流程設定

> 版本：v1.5
> 更新日期：2026-09-04
> 語系偏好：繁體中文（Taiwan）

這份懶人包的目標，是讓 Anti-Gravity 使用者能安全連接 NotebookLM、Firebase、GitHub、Obsidian，並建立「開工 / 收工 / 新專案初始化」工作流程。本版本對齊 AntiGravity 2 寫法：規則入口用 `AGENTS.md`、技能放 `.agents/skills/`、NotebookLM MCP 用 `nlm setup add antigravity`；Obsidian 保留為專案筆記（AntiGravity 直接讀寫 vault），不安裝 MCPVault。

本文件只放可公開教學的設定流程，不放任何個人 NotebookLM 清單、筆記本 ID、研究報告、生成圖片、帳號 token 或測試專案。

---

## 先備條件

- [ ] 已安裝 AntiGravity 2（`agy`）或可使用 MCP 的 AI 編碼助理
- [ ] 已安裝 Git
- [ ] 已安裝 GitHub CLI（`gh`）
- [ ] 已安裝 Node.js / npm
- [ ] 已安裝 Python 或 `uv`
- [ ] 有 Google 帳號，可登入 NotebookLM / Firebase
- [ ] 有 GitHub 帳號
- [ ] 已有 Obsidian vault，或知道筆記本資料夾位置

---

## 一、連接 NotebookLM

### 重點原則

`notebooklm-mcp-cli` 是第三方工具，`nlm login` 會開啟一個由它管理的獨立瀏覽器視窗取得 session，不是標準 Google OAuth，也不要去按 AntiGravity 的 MCP OAuth 按鈕。不要複製 cookie、token，也不要把 NotebookLM 匯出的 `notebooks.json` 或筆記本 ID 清單放進公開 repo。

### 安裝 NotebookLM MCP CLI

建議優先用 `uv` 安裝：

```bash
uv tool install notebooklm-mcp-cli
nlm --version
```

如果沒有 `uv`，再用 pip：

```bash
pip install notebooklm-mcp-cli
nlm --version
```

### 重新登入 Google 帳號

請在一般、可見的 Terminal 視窗親自執行（不要在 AntiGravity 背景 terminal 反覆跑）。若曾經登入錯帳號，先登出再重新登入：

```bash
export PYTHONUTF8=1
nlm logout
nlm config set auth.browser chrome
nlm login --profile default
```

`nlm login` 會開啟一個由 `nlm` 管理的獨立 Chrome 視窗，請在裡面選擇正確的 Google 帳號完成登入。

驗證：

```bash
nlm doctor
nlm list
```

### 註冊 MCP

AntiGravity 2 直接用 `nlm` 內建的設定指令，修改前先預告並取得確認：

```bash
nlm setup add antigravity
```

---

## 二、連接 GitHub

### 登入 GitHub CLI

```bash
gh auth status
gh auth login --web --git-protocol https
gh auth status
```

### 設定 Git 使用者

```bash
git config --global user.name "你的名字"
git config --global user.email "your-email@example.com"
```

---

## 三、連接 Firebase

### 安裝與登入

```bash
npx -y firebase-tools@latest --version
npx -y firebase-tools@latest login
npx -y firebase-tools@latest projects:list
```

### 註冊 Firebase MCP

寫進 AntiGravity 2 的 MCP 設定檔（workspace `.agents/mcp_config.json` 或全域 `~/.gemini/config/mcp_config.json`）：

```json
{
  "mcpServers": {
    "firebase": {
      "command": "npx",
      "args": ["-y", "firebase-tools@latest", "mcp"]
    }
  }
}
```

---

## 四、連接 Obsidian

AntiGravity 2 可以直接讀寫檔案，Obsidian vault 就是一般 Markdown 資料夾，不必安裝任何 MCP server：
- 把 vault 路徑與專案駕駛艙位置寫進專案 `AGENTS.md` 的「Obsidian 對應筆記」欄位。
- 在 vault 內建立 `<專案名稱>/專案工作流程.md` 記錄進度。

---

## 五、開工 / 收工 / 新專案初始化

### 開工

使用者說「開工」時，AI 應：
1. 讀取專案根目錄的 `AGENTS.md`。
2. 讀取 Obsidian 專案駕駛艙（若有）。
3. 執行 `git status` 與最近 commit 檢查。
4. 回報目前狀態與建議下一步。

### 收工

使用者說「收工」時，AI 應：
1. 檢查是否有敏感資料。
2. 更新 Obsidian 專案駕駛艙（若有）。
3. 執行 `git status` 與 diff 檢查。
4. 只 stage 本次相關檔案。
5. 產生 commit message，確認後 commit / push。
