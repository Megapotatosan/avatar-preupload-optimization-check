# Avatar Pre-Upload Optimization Check

[English](README.md) | [日本語](README.ja.md) | **繁體中文（台灣）**

一個讓 **AI 代理（agent）在上傳 VRChat Avatar 前檢查並最佳化**的 skill。它針對 VCC / ALCOM 管理的 Unity 專案做上傳前 QA，以畫質為優先。可以在 Claude Code、Claude 應用程式（claude.ai / 桌面版 / Cowork）、OpenAI Codex，以及任何能讀取 `SKILL.md` 格式 skill 的代理中使用。

你只要說「上傳前幫我檢查 Avatar」，代理就會依序：

1. **預先檢查專案（唯讀）。** 確認必要套件都已安裝並 Resolve、版本彼此相容；也會找出殘留的舊 `.unitypackage` 檔案，並找到你的 Avatar。
2. **測量 VRChat 實際收到的狀態。** SDK 面板顯示的是 NDMF 處理前的數字，所以會把 Avatar 複製一份、跑過 NDMF 再測量。
3. **套用不影響外觀的非破壞性最佳化。** 使用 AAO Trace And Optimize 和 LAC Texture Compressor，合併常駐顯示的網格，並刪除被衣服蓋住的身體多邊形。
4. **（只在你要求時）朝指定等級減面。** 用 Meshia 減少多邊形，每個部位都有依實際遊戲內問題訂出的減面上限；也可以用 VRCQuestTools 做行動版轉換。
5. **驗證並產生報告。** 比對截圖、擺手指姿勢檢查、執行靜態檢查，並寫出附還原步驟的報告。

它**絕對不會幫你上傳**。Publish 按鈕由你自己按。

> 本專案與 VRChat Inc. 及下列工具的作者無關。

---

## 為什麼以畫質為優先？

| 事實（VRChat 官方文件，2026-10） | 代表什麼 |
|---|---|
| PC 的 **Good、Medium、Poor 三角面上限都是 70,000** | 降到 Poor 只會多出材質數、網格數和貼圖記憶體，不會多出三角面 |
| PC 的「最低顯示效能等級」預設是 **Very Poor** | 大部分 PC 玩家照樣看得到 Very Poor 的 Avatar |
| 行動版預設會隱藏 **Poor 和 Very Poor** | 要做行動版的話，至少要達到行動版 **Medium** 才有意義 |

因此預設會在**完全不改變外觀**的前提下減輕負擔，PC 結果是 Very Poor 也接受。如果想追某個等級（例如「做到 PC Medium」），直接這樣要求即可。skill 會切換到 `rank_target` 模式，並在動手前先說明外觀會受到什麼影響。

## 需求

| | |
|---|---|
| Unity 專案 | 由 **VCC 或 ALCOM** 管理的 VRChat Avatar 專案（Unity 2022.3） |
| 必要套件 | VRChat SDK（Base、Avatars）、**NDMF**、**AAO: Avatar Optimizer** |
| 建議套件 | **LAC（Avatar Compressor）**、**lilAvatarUtils**、**Meshia Mesh Simplification**；行動版需要 **VRCQuestTools** |
| Python | 專案所在電腦需有 3.8 以上（執行唯讀預檢用） |
| Unity 連線（選用，建議） | [MCP for Unity](https://github.com/CoplayDev/unity-mcp)，需要 Git 和 [uv](https://docs.astral.sh/uv/)。沒有的話會進入「引導手動模式」：代理告訴你要點哪裡，你再回報結果 |

這些全部會在第 0 階段由 skill 幫你檢查，並具體告訴你要在 VCC / ALCOM 加入哪些套件。

## 安裝

### 交給你的代理

把下面這段貼給你的代理：

```text
Install the agent skill from https://github.com/Megapotatosan/avatar-preupload-optimization-check
by following INSTALL-FOR-AGENTS.md in that repository.
```

[INSTALL-FOR-AGENTS.md](INSTALL-FOR-AGENTS.md) 是寫給代理看的安裝說明。內容包括判斷執行環境、各平台的確切指令、驗證方式，以及更新和移除。

### 手動安裝

<details>
<summary><b>Claude Code</b>（外掛市集，建議）</summary>

```text
/plugin marketplace add Megapotatosan/avatar-preupload-optimization-check
/plugin install avatar-preupload-optimization-check@megapotatosan-vrchat
/reload-plugins
```

也可以不用外掛系統，直接裝成個人 skill：

```bash
git clone https://github.com/Megapotatosan/avatar-preupload-optimization-check
cp -r avatar-preupload-optimization-check/skills/avatar-preupload-optimization-check ~/.claude/skills/
```
</details>

<details>
<summary><b>Claude 應用程式</b>（claude.ai / 桌面版 / Cowork）</summary>

1. 從 [Releases](https://github.com/Megapotatosan/avatar-preupload-optimization-check/releases) 下載 `avatar-preupload-optimization-check.zip`，或用 `python tools/build_zip.py` 自己打包。
2. 開啟**程式碼執行與檔案建立**。
3. 到**設定 → 功能（Capabilities）→ Skills → 上傳 skill**，選擇那個 ZIP 檔。

需要 Pro、Max、Team 或 Enterprise 方案。要讓 skill 存取你的 Unity 專案，請使用已連接專案資料夾的桌面版，或使用 Claude Code。
</details>

<details>
<summary><b>OpenAI Codex</b>（CLI / IDE）</summary>

```bash
git clone https://github.com/Megapotatosan/avatar-preupload-optimization-check
mkdir -p ~/.agents/skills
cp -r avatar-preupload-optimization-check/skills/avatar-preupload-optimization-check ~/.agents/skills/
```

只想在某個 repository 使用的話，改放到 `<repo>/.agents/skills/`。如果 skill 沒有出現，請重新啟動 Codex。
</details>

<details>
<summary><b>其他代理</b></summary>

把 `skills/avatar-preupload-optimization-check/` 複製到代理的 skills 資料夾。沒有 skill 功能的代理，請告訴它「讀取 `SKILL.md` 並照著做」。
</details>

## 連接 Unity（選用，建議）

skill 可以透過 **MCP for Unity**（支援 Unity 2021.3–6.x）操作開著的 Unity Editor。Unity 官方的 MCP 只支援 Unity 6，所以不能用在 VRChat 的 Unity 2022.3。

1. 安裝 **Git** 和 **uv**，然後重新啟動 Unity。
2. 在 Unity 的 **Package Manager → Add package from git URL** 輸入：
   `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0`
3. 打開 **Window → MCP for Unity**，選擇你的代理（Claude Desktop、Claude Code、Codex、Cursor…），按 **Configure**。
4. 完全關閉代理程式再重新開啟。

這些步驟也寫在 skill 裡，可以讓代理一步一步帶你做。

## 使用方式

```text
上傳前幫我檢查 Avatar，專案在 E:\VRC\MyProject
```

```text
這個 Avatar 能做到 PC Medium 嗎？臉和手不要動。
```

你會得到：

- 每個 Avatar 一份設定檔 `<project>/.avatar-preupload/<Avatar>.profile.yaml`，記錄要保護的部位、移除的物件和模式。
- 一份報告 `<project>/.avatar-preupload/reports/<日期>-<Avatar>.md`，包含前後數字、每項變更和還原方法。
- 截圖放在 `<project>/.avatar-preupload/screenshots/`。
- 所有變更都是 NDMF 元件或場景上實例的修改，並記錄在 Unity 的 Undo 裡。請自己儲存場景（Ctrl+S），再從 VRChat SDK 上傳。

### 各部位減面上限（`rank_target` 模式）

這些上限來自遊戲內實際發生過的問題：

| 部位 | 上限 | 超過會 |
|---|---|---|
| 臉（臉部追蹤） | 0% | 表情、對嘴變形 |
| 手、手指 | 約 30%（先從身體網格拆出來） | 手指變形 |
| 貼身衣物 | 約 25% | 皮膚穿出衣服 |
| 頭髮 | 每款頭髮個別測試（約 33% 沒問題） | 頭髮破洞 |
| 小飾品 | 最多約 85% | — |

## 專案結構

```
.claude-plugin/            Claude Code 外掛與市集設定
skills/avatar-preupload-optimization-check/
  SKILL.md                 skill 本體（可獨立運作，附錄 A 內含 precheck.py）
  scripts/precheck.py      第 0 階段預檢（只用標準函式庫、唯讀）
tests/                     模擬 VCC 專案與單元測試
tools/build_zip.py         產生 Claude 應用程式用的 ZIP
INSTALL-FOR-AGENTS.md      寫給 AI 代理的安裝說明
```

## 開發

```bash
python -m unittest discover -s tests -v   # 預檢測試 + 檢查 SKILL.md 與腳本是否一致
python tools/build_zip.py                 # -> dist/avatar-preupload-optimization-check.zip
claude plugin validate .                  # 有安裝 Claude Code 的話
```

`SKILL.md` 的附錄 A 必須和 `scripts/precheck.py` 完全相同，測試會檢查這點。推送 `v*` 標籤會自動建立附帶 ZIP 的 Release。

## 致謝

這個 skill 是把以下優秀的工具串在一起使用，請支持原作者：

- [AAO: Avatar Optimizer](https://vpm.anatawa12.com/avatar-optimizer/)（anatawa12）
- [NDMF](https://ndmf.nadena.dev/) / [Modular Avatar](https://modular-avatar.nadena.dev/)（bd_）
- [LAC: Avatar Compressor](https://lac.limitex.dev/)（Limitex）
- [Meshia Mesh Simplification](https://github.com/RamType0/Meshia.MeshSimplification)（RamType0）
- [VRCQuestTools](https://kurotu.github.io/VRCQuestTools/)（kurotu）
- [lilAvatarUtils](https://github.com/lilxyzw/lilAvatarUtils)（lilxyzw）
- [MCP for Unity](https://github.com/CoplayDev/unity-mcp)（CoplayDev）

## 授權

[MIT](LICENSE)
