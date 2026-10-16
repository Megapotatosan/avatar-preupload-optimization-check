# Avatar Pre-Upload Optimization Check

[English](README.md) | **日本語** | [繁體中文（台灣）](README.zh-TW.md)

VRChat アバターのアップロード前チェックと軽量化を行う **AI エージェント用スキル**です。VCC / ALCOM 管理の Unity プロジェクトを対象に、見た目を優先して QA を進めます。Claude Code、Claude アプリ（claude.ai / デスクトップ / Cowork）、OpenAI Codex のほか、`SKILL.md` 形式のスキルを読めるエージェントで使えます。

「アップロード前にアバターをチェックして」と頼むと、エージェントは次の順で作業します。

1. **プロジェクトの事前チェック（読み取り専用）。** 必要なパッケージが入っているか、Resolve 済みか、バージョンが噛み合っているかを確認します。古い `.unitypackage` の残りや、アバターの場所も調べます。
2. **実際に VRChat に届く状態を計測。** SDK パネルの数値は NDMF 適用前のものなので、アバターの複製に NDMF を通して計測します。
3. **見た目が変わらない非破壊の軽量化を適用。** AAO Trace And Optimize と LAC Texture Compressor を使い、常時表示メッシュを統合し、服に隠れた素体ポリゴンを削除します。
4. **ランク狙いの軽量化（頼まれたときだけ）。** Meshia でポリゴンを削減します。削減率には、実際のゲーム内の不具合から得た部位ごとの上限があります。VRCQuestTools でモバイル対応もできます。
5. **検証とレポート。** スクリーンショットの比較、指ポーズの確認、静的チェックを行い、元に戻す手順付きのレポートを書きます。

**アップロードは絶対にしません。** Publish はご自身で押してください。

> VRChat Inc. および下記ツールの作者とは無関係の非公式プロジェクトです。

---

## なぜ見た目優先なのか

| 事実（VRChat 公式ドキュメント、2026-10 時点） | 意味 |
|---|---|
| PC の **Good / Medium / Poor はポリゴン上限がすべて 70,000** | Poor に下げても増えるのはマテリアル数・メッシュ数・テクスチャメモリだけで、ポリゴンは増えない |
| PC の「最低表示パフォーマンスランク」の初期値は **Very Poor** | PC ユーザーの大半には Very Poor でも表示される |
| モバイルの初期設定では **Poor と Very Poor が非表示** | モバイル版を作るなら **Medium** 以上が目安 |

そのため初期設定では、**見た目を一切変えずに**軽くし、結果が PC Very Poor でも受け入れます。特定のランクを狙いたいとき（例：「PC Medium にして」）は、そう頼んでください。スキルは `rank_target` モードに切り替わり、変更する前に見た目への影響を説明します。

## 動作要件

| | |
|---|---|
| Unity プロジェクト | **VCC / ALCOM** で管理された VRChat アバタープロジェクト（Unity 2022.3） |
| 必須パッケージ | VRChat SDK（Base / Avatars）、**NDMF**、**AAO: Avatar Optimizer** |
| 推奨 | **LAC（Avatar Compressor）**、**lilAvatarUtils**、**Meshia Mesh Simplification**、モバイル向けに **VRCQuestTools** |
| Python | プロジェクトがある PC に 3.8 以上（読み取り専用の事前チェック用） |
| Unity 連携（任意・推奨） | [MCP for Unity](https://github.com/CoplayDev/unity-mcp)。Git と [uv](https://docs.astral.sh/uv/) が必要です。連携しない場合は「手順案内モード」になり、エージェントの指示どおりに操作して結果を伝えます |

これらはすべてフェーズ 0 でスキルが確認し、VCC / ALCOM で何を追加すればよいかを具体的に案内します。

## インストール

### エージェントに任せる

エージェントに次の文を貼り付けてください。

```text
Install the agent skill from https://github.com/Megapotatosan/avatar-preupload-optimization-check
by following INSTALL-FOR-AGENTS.md in that repository.
```

[INSTALL-FOR-AGENTS.md](INSTALL-FOR-AGENTS.md) はエージェント向けの手順書です。実行環境の判別、プラットフォームごとのコマンド、確認方法、更新とアンインストールを扱っています。

### 手動インストール

<details>
<summary><b>Claude Code</b>（プラグインマーケットプレイス、推奨）</summary>

```text
/plugin marketplace add Megapotatosan/avatar-preupload-optimization-check
/plugin install avatar-preupload-optimization-check@megapotatosan-vrchat
/reload-plugins
```

プラグイン機能を使わず、個人スキルとして入れることもできます。

```bash
git clone https://github.com/Megapotatosan/avatar-preupload-optimization-check
cp -r avatar-preupload-optimization-check/skills/avatar-preupload-optimization-check ~/.claude/skills/
```
</details>

<details>
<summary><b>Claude アプリ</b>（claude.ai / デスクトップ / Cowork）</summary>

1. [Releases](https://github.com/Megapotatosan/avatar-preupload-optimization-check/releases) から `avatar-preupload-optimization-check.zip` をダウンロードします。`python tools/build_zip.py` で自分で作ることもできます。
2. **コード実行とファイル作成**をオンにします。
3. **設定 → 機能（Capabilities）→ スキル → スキルをアップロード** で ZIP を選びます。

Pro / Max / Team / Enterprise プランが必要です。スキルから Unity プロジェクトを触るには、プロジェクトフォルダを接続したデスクトップアプリか、Claude Code を使ってください。
</details>

<details>
<summary><b>OpenAI Codex</b>（CLI / IDE）</summary>

```bash
git clone https://github.com/Megapotatosan/avatar-preupload-optimization-check
mkdir -p ~/.agents/skills
cp -r avatar-preupload-optimization-check/skills/avatar-preupload-optimization-check ~/.agents/skills/
```

特定のリポジトリだけで使う場合は `<repo>/.agents/skills/` に置きます。スキルが表示されないときは Codex を再起動してください。
</details>

<details>
<summary><b>その他のエージェント</b></summary>

`skills/avatar-preupload-optimization-check/` をエージェントのスキルフォルダにコピーします。スキル機能がないエージェントには「`SKILL.md` を読んで従って」と伝えてください。
</details>

## Unity との連携（任意・推奨）

スキルは **MCP for Unity**（Unity 2021.3〜6.x 対応）を通じて、開いている Unity Editor を操作できます。Unity 公式の MCP は Unity 6 専用なので、VRChat の Unity 2022.3 では使えません。

1. **Git** と **uv** をインストールし、Unity を再起動します。
2. Unity の **Package Manager → Add package from git URL** に次を入力します。
   `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0`
3. **Window → MCP for Unity** を開き、使うエージェント（Claude Desktop / Claude Code / Codex / Cursor など）を選んで **Configure** を押します。
4. エージェントのアプリを完全に終了してから起動し直します。

この手順はスキルにも入っているので、エージェントに案内してもらうこともできます。

## 使い方

```text
アップロード前にアバターをチェックして。プロジェクトは E:\VRC\MyProject
```

```text
このアバターは PC Medium にできる？顔と手は削らないで。
```

出力されるもの：

- アバターごとのプロファイル `<project>/.avatar-preupload/<Avatar>.profile.yaml`。保護する部位、外したアイテム、モードを記録します。
- レポート `<project>/.avatar-preupload/reports/<日付>-<Avatar>.md`。変更前後の数値、すべての変更点、元に戻す方法をまとめます。
- スクリーンショット `<project>/.avatar-preupload/screenshots/`。
- 変更はすべて NDMF コンポーネントかシーン上のインスタンスへの変更で、Unity の Undo に記録されます。シーンの保存（Ctrl+S）とアップロードはご自身で行ってください。

### 部位ごとの削減上限（`rank_target` モード）

ゲーム内で実際に起きた不具合をもとにしています。

| 部位 | 上限 | 超えると |
|---|---|---|
| 顔（フェイストラッキング） | 0% | 表情・リップシンクの崩れ |
| 手・指 | 約 30%（素体メッシュから分離したうえで） | 指の変形 |
| 体に密着した服 | 約 25% | 肌の貫通 |
| 髪 | 髪ごとに検証（約 33% は問題なし） | 髪に穴が空く |
| 小物アクセサリー | 最大約 85% | — |

## リポジトリ構成

```
.claude-plugin/            Claude Code のプラグイン／マーケットプレイス定義
skills/avatar-preupload-optimization-check/
  SKILL.md                 スキル本体（単体で動作。付録 A に precheck.py を同梱）
  scripts/precheck.py      フェーズ 0 の事前チェック（標準ライブラリのみ・読み取り専用）
tests/                     ダミーの VCC プロジェクトとユニットテスト
tools/build_zip.py         Claude アプリ用 ZIP の作成
INSTALL-FOR-AGENTS.md      AI エージェント向けインストール手順
```

## 開発

```bash
python -m unittest discover -s tests -v   # 事前チェックのテスト + SKILL.md とスクリプトの一致確認
python tools/build_zip.py                 # -> dist/avatar-preupload-optimization-check.zip
claude plugin validate .                  # Claude Code がある場合
```

`SKILL.md` の付録 A は `scripts/precheck.py` と完全に同一である必要があり、テストで確認しています。`v*` タグを push すると、ZIP 付きのリリースが自動で作成されます。

## クレジット

このスキルは次のすばらしいツールを組み合わせて使っています。ぜひ作者を応援してください。

- [AAO: Avatar Optimizer](https://vpm.anatawa12.com/avatar-optimizer/)（anatawa12 さん）
- [NDMF](https://ndmf.nadena.dev/) / [Modular Avatar](https://modular-avatar.nadena.dev/)（bd_ さん）
- [LAC: Avatar Compressor](https://lac.limitex.dev/)（Limitex さん）
- [Meshia Mesh Simplification](https://github.com/RamType0/Meshia.MeshSimplification)（RamType0 さん）
- [VRCQuestTools](https://kurotu.github.io/VRCQuestTools/)（kurotu さん）
- [lilAvatarUtils](https://github.com/lilxyzw/lilAvatarUtils)（lilxyzw さん）
- [MCP for Unity](https://github.com/CoplayDev/unity-mcp)（CoplayDev）

## ライセンス

[MIT](LICENSE)
