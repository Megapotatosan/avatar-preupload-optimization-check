# Avatar Pre-Upload Optimization Check

**English** | [日本語](README.ja.md) | [繁體中文（台灣）](README.zh-TW.md)

An **agent skill** that checks and optimizes a VRChat avatar before you upload it. It is a quality-first pre-upload QA routine for VCC/ALCOM Unity projects. It runs in Claude Code, the Claude app (claude.ai, desktop, Cowork), OpenAI Codex, and any other agent that reads `SKILL.md` skills.

You say "check my avatar before upload". The agent then:

1. **Pre-checks the project.** It confirms the required packages are installed and resolved and that their versions are compatible. It also finds leftover `.unitypackage` copies and locates your avatars. This step is read-only.
2. **Audits what VRChat will actually receive.** It processes a clone of the avatar through NDMF and measures that, because the SDK panel shows numbers from before NDMF runs.
3. **Applies lossless, non-destructive optimizations,** using AAO Trace And Optimize, LAC Texture Compressor, merging always-on meshes, and removing body polygons hidden under clothes.
4. **Optionally targets a performance rank,** only if you ask. It reduces polygons with Meshia, with per-part caps learned from real in-game failures, and can convert for mobile with VRCQuestTools.
5. **Validates and reports.** It compares screenshots, poses the fingers, runs static checks, and writes a report with undo steps.

It **never uploads**. You press Publish yourself.

> Not affiliated with VRChat Inc. or with the authors of the tools listed below.

---

## Why quality-first?

| Fact (VRChat docs, 2026-10) | Consequence |
|---|---|
| PC **Good, Medium and Poor all share the same 70,000-triangle limit** | Dropping to Poor buys more material slots, meshes and texture memory, but no extra triangles |
| PC's default *Minimum displayed performance rank* is **Very Poor** | Most PC users still see a Very Poor avatar |
| Mobile's default hides **Poor and Very Poor** | A mobile build is only worth making at mobile **Medium** or better |

So by default the skill makes the avatar cheaper **without any visible change**, and accepts whatever PC rank results. To chase a rank (for example "make it PC Medium"), ask for it. The skill then switches to `rank_target` mode and shows you the visual trade-off before it changes anything.

## Requirements

| | |
|---|---|
| Unity project | A VRChat avatar project managed by **VCC or ALCOM** (Unity 2022.3) |
| Required packages | VRChat SDK (Base and Avatars), **NDMF**, **AAO: Avatar Optimizer** |
| Recommended | **LAC (Avatar Compressor)**, **lilAvatarUtils**, **Meshia Mesh Simplification**; **VRCQuestTools** for mobile |
| Python | 3.8+ on the machine that holds the project (for the read-only pre-check) |
| Unity bridge (optional, recommended) | [MCP for Unity](https://github.com/CoplayDev/unity-mcp), which needs Git and [uv](https://docs.astral.sh/uv/). Without it, the skill runs in guided-manual mode: it tells you what to click and you report back |

The skill checks all of these for you in Phase 0 and tells you exactly what to add in VCC/ALCOM.

## Install

### Let your agent do it

Paste this into your agent:

```text
Install the agent skill from https://github.com/Megapotatosan/avatar-preupload-optimization-check
by following INSTALL-FOR-AGENTS.md in that repository.
```

[INSTALL-FOR-AGENTS.md](INSTALL-FOR-AGENTS.md) is written for agents. It covers detecting the environment, the exact commands for each platform, verification, updates and uninstalling.

### Manual install

<details>
<summary><b>Claude Code</b> (plugin marketplace, recommended)</summary>

```text
/plugin marketplace add Megapotatosan/avatar-preupload-optimization-check
/plugin install avatar-preupload-optimization-check@megapotatosan-vrchat
/reload-plugins
```

Or, as a personal skill without the plugin system:

```bash
git clone https://github.com/Megapotatosan/avatar-preupload-optimization-check
cp -r avatar-preupload-optimization-check/skills/avatar-preupload-optimization-check ~/.claude/skills/
```
</details>

<details>
<summary><b>Claude app</b> (claude.ai, desktop, Cowork)</summary>

1. Download `avatar-preupload-optimization-check.zip` from [Releases](https://github.com/Megapotatosan/avatar-preupload-optimization-check/releases), or build it with `python tools/build_zip.py`.
2. Turn on **Code execution and file creation**.
3. Go to **Settings → Capabilities → Skills → Upload skill** and choose the ZIP.

You need a Pro, Max, Team or Enterprise plan. To let the skill reach your Unity project, use the desktop app with your project folder connected, or Claude Code.
</details>

<details>
<summary><b>OpenAI Codex</b> (CLI / IDE)</summary>

```bash
git clone https://github.com/Megapotatosan/avatar-preupload-optimization-check
mkdir -p ~/.agents/skills
cp -r avatar-preupload-optimization-check/skills/avatar-preupload-optimization-check ~/.agents/skills/
```

To make it available in one repository only, use `<repo>/.agents/skills/` instead. Restart Codex if the skill doesn't show up.
</details>

<details>
<summary><b>Other agents</b></summary>

Copy `skills/avatar-preupload-optimization-check/` into your agent's skills folder. If your agent has no skill system, tell it to read `SKILL.md` and follow it.
</details>

## Connect Unity (optional, recommended)

The skill can drive the open Unity Editor through **MCP for Unity**, which supports Unity 2021.3–6.x. Unity's own MCP needs Unity 6, so it doesn't work with VRChat's Unity 2022.3.

1. Install **Git** and **uv**, then restart Unity.
2. In Unity, open **Package Manager → Add package from git URL**:
   `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0`
3. Open **Window → MCP for Unity**, pick your agent (Claude Desktop, Claude Code, Codex, Cursor, …) and click **Configure**.
4. Restart your agent app completely.

Your agent can also walk you through these steps; they are in the skill.

## Usage

```text
Check my avatar before upload. The project is at E:\VRC\MyProject
```

```text
Can this avatar reach PC Medium? Keep the face and hands untouched.
```

What you get:

- A profile per avatar at `<project>/.avatar-preupload/<Avatar>.profile.yaml`. It records protected parts, removed items and the mode.
- A report at `<project>/.avatar-preupload/reports/<date>-<Avatar>.md` with before/after numbers, every change and how to undo it.
- Screenshots in `<project>/.avatar-preupload/screenshots/`.
- All changes are NDMF components or scene-instance edits, recorded with Unity Undo. Save the scene (Ctrl+S) yourself, then upload from the VRChat SDK.

### Per-part reduction caps (`rank_target` mode)

These caps come from defects seen in-game:

| Part | Max cut | Beyond it |
|---|---|---|
| Face (face tracking) | 0% | Expression and lip-sync deformation |
| Hands / fingers | ~30%, after splitting them from the body mesh | Distorted fingers |
| Skin-tight clothing | ~25% | Skin pokes through |
| Hair cards | Test per hair (~33% was clean) | Holes in the hair |
| Small accessories | up to ~85% | — |

## Repository layout

```
.claude-plugin/            Claude Code plugin + marketplace manifests
skills/avatar-preupload-optimization-check/
  SKILL.md                 the skill (self-contained; embeds precheck.py as Appendix A)
  scripts/precheck.py      Phase 0 pre-check, stdlib only, read-only
tests/                     mock VCC projects + unit tests
tools/build_zip.py         builds the ZIP for the Claude app
INSTALL-FOR-AGENTS.md      install guide written for AI agents
```

## Development

```bash
python -m unittest discover -s tests -v   # pre-check tests + SKILL.md/script sync check
python tools/build_zip.py                 # -> dist/avatar-preupload-optimization-check.zip
claude plugin validate .                  # if you have Claude Code
```

`SKILL.md` Appendix A must stay byte-identical to `scripts/precheck.py`; the tests enforce this. Pushing a `v*` tag publishes a release with the ZIP attached.

## Credits

This skill orchestrates these excellent tools. Please support their authors:

- [AAO: Avatar Optimizer](https://vpm.anatawa12.com/avatar-optimizer/) (anatawa12)
- [NDMF](https://ndmf.nadena.dev/) and [Modular Avatar](https://modular-avatar.nadena.dev/) (bd_)
- [LAC: Avatar Compressor](https://lac.limitex.dev/) (Limitex)
- [Meshia Mesh Simplification](https://github.com/RamType0/Meshia.MeshSimplification) (RamType0)
- [VRCQuestTools](https://kurotu.github.io/VRCQuestTools/) (kurotu)
- [lilAvatarUtils](https://github.com/lilxyzw/lilAvatarUtils) (lilxyzw)
- [MCP for Unity](https://github.com/CoplayDev/unity-mcp) (CoplayDev)

## License

[MIT](LICENSE)
