---
name: "avatar-preupload-optimization-check"
description: "Agent-neutral, quality-first pre-upload QA for a VRChat avatar in a VCC/ALCOM Unity project: package check, NDMF-processed audit, lossless AAO/LAC optimization, Meshia/VQT only on request. Never uploads."
---

# Avatar Pre-Upload Optimization Check

Use this skill when the user has finished editing a VRChat avatar and wants it checked and optimized before upload. Typical requests: "幫我檢查 Avatar 準備上傳", "pre-upload check", "optimize my avatar", "can it reach Medium?".

You act as a **pre-upload QA assistant**, not a blind optimizer. **Visual quality comes first.** The default is to make the avatar cheaper without any visible change, and to accept whatever PC rank that gives, **including Very Poor**. Chase a specific rank only when the user asks for one, and then show the visual cost before applying it. The user always presses Publish themselves.

**Why Very Poor is an acceptable PC result:**
- PC Good, Medium and Poor all share the same 70,000-triangle limit. Dropping to Poor buys more material slots, meshes and texture memory, but no extra triangles.
- PC's default "Minimum displayed performance rank" is Very Poor, so most PC users still see a Very Poor avatar.
- Mobile is different: its default hides Poor and Very Poor. A mobile build is only worth making at mobile **Medium** or better.

This skill is written for any coding agent: Claude (Cowork, the desktop app, Claude Code), ChatGPT (Codex CLI or the IDE extension), Cursor, and others. Where an instruction depends on the agent, it names a capability ("a shell on the user's machine", "a Unity bridge"), not a product-specific tool.

## Capabilities this skill uses

| Capability | Needed for | If missing |
|---|---|---|
| Read files in the Unity project (a shell or file access on the user's machine) | Phase 0 pre-check script | Ask the user to run `precheck.py` themselves and paste the output |
| A Unity Editor bridge that can run C# in the open Editor (MCP for Unity, see below) | Phases 1–4: exact numbers, adding components, screenshots | Guided-manual mode: give step-by-step instructions, and the user reports numbers and screenshots |
| Web access | Fetching current rank limits | Use the fallback table and say so |

**Platform notes**

| Agent | Shell on the user's PC | Unity bridge |
|---|---|---|
| Claude desktop app / Cowork, or a cloud session linked to the user's computer | Yes, through the computer link once the project folder is connected (paths look like `$HOME/mnt/<folder>`) | Register MCP for Unity under **Claude Desktop**. Its tools then appear proxied, for example `…unityMCP__execute_code` |
| Claude Code (local) | Yes, the native shell | Register under **Claude Code** |
| ChatGPT via Codex CLI or the IDE extension | Yes, Codex's shell | Register under **Codex**. MCP for Unity writes the Codex MCP config |
| ChatGPT chat without a local agent | No | Guided-manual mode only |
| Cursor, VS Code Copilot, Windsurf, Gemini CLI, and others | Usually yes | MCP for Unity lists 20+ clients |

## Hard rules

1. **Never upload or publish.** Stop at the report. The user uploads from the VRChat SDK Builder.
2. **Phase 0 comes first and blocks.** Do no audit or optimization until Phase 0 has no FAIL.
3. **Prefer non-destructive changes.** Add NDMF components or change settings on the avatar's scene instance. Don't edit FBX, meshes, materials, textures or import settings unless the user approves each one.
4. **Back up before the first change.** Accept a git commit, a VCC/ALCOM backup, or the user's explicit "go ahead without backup".
5. **Respect approval tiers.** You may apply Phase 2 changes automatically if the profile allows it. Phase 3 changes need an explicit yes, either per item or for a reviewed batch.
6. **Respect the profile.** Anything under `protected` is never merged away, simplified, removed, downscaled or pruned.
7. **Don't install packages silently.** Tell the user what to add in VCC/ALCOM. Run `vrc-get install <id>` only if the user asks you to.
8. **Report in the user's language.** Keep tool and component names in English.
9. **Don't hard-code thresholds.** Fetch the current limits from https://creators.vrchat.com/avatars/avatar-performance-ranking-system/ . Use the fallback table only if you can't reach the page, and say so.
10. **Make every change undoable.** Use `Undo.*` and record prefab-instance modifications. Don't save the scene for the user: tell them to press Ctrl+S at the end.

## Inputs to settle (ask only what you can't discover)

- **Unity project folder**: the one containing `Assets/`, `Packages/` and `ProjectSettings/`.
- **Which avatar**: Phase 0 and the Unity bridge both list avatars. Ask only when there is more than one candidate. Avatars usually live as instances in a scene.
- **Target platform**: `pc`, `mobile` or `both`. **Ask before running Phase 0 with `--target both`**, because that turns a missing VRCQuestTools into a FAIL.
- **Mode** (default `quality_first`):
  - `quality_first`: Phase 2 plus lossless Phase 3 items only (EditorOnly removal of things the user agrees to drop, merging always-on meshes, removing body hidden under clothes). No polygon reduction. Any resulting PC rank, Very Poor included, is fine.
  - `rank_target`: the user names a rank, for example "PC Medium". Polygon reduction is allowed within the per-part caps in Phase 3, and you must show the visual trade-off first.
- **Target rank** (only in `rank_target` mode): ask which one. For mobile, recommend Medium, since mobile hides Poor and Very Poor by default.
- **Profile**: `<project>/.avatar-preupload/<AvatarName>.profile.yaml`. Create it with the user on the first run and reuse it later.

## Phase 0 — Project pre-check (read-only, blocking)

Run `precheck.py` against the project folder. Use `scripts/precheck.py` next to this SKILL.md if it exists (repository and plugin installs ship it). Otherwise write Appendix A, which is the same file, to a temp location. It needs Python 3.8+, uses only the standard library, and never writes to the project.

- Local shell: `python precheck.py "<project>" --target pc|mobile|both`. On Windows, `py` may replace `python`.
- Linked-computer shell (a Linux VM with the folder mounted): write the script to `$HOME/precheck.py`, then run `python3 $HOME/precheck.py "$HOME/mnt/<folder>"`.
- Options: `--unity-editor "<Hub>/Editor/<ver>/Editor"` also checks Android Build Support. `--json` gives machine-readable output.
- **Run time:** about 2–3 minutes on a real project read through a linked-computer mount, because it indexes `Library/PackageCache`. Allow a timeout of at least 180 s.

**What it checks**

| Check | Result |
|---|---|
| Project type | FAIL if `Packages/vpm-manifest.json` is missing (not VCC/ALCOM managed) |
| Unity version | WARN if not 2022.3.x |
| Packages resolved | FAIL if a package in `vpm-manifest.json` is missing from `Packages/` (the same comparison the VCC Resolver makes) |
| Required packages | FAIL if `com.vrchat.base`, `com.vrchat.avatars`, `nadena.dev.ndmf` or `com.anatawa12.avatar-optimizer` is missing, or `com.github.kurotu.vrc-quest-tools` when the target includes mobile |
| Recommended packages | WARN if LAC (`dev.limitex.avatar-compressor`), `jp.lilxyzw.avatar-utils` or a polygon reducer is missing |
| Polygon reducer | Meshia (`com.ramtype0.meshia.mesh-simplification`), or Mantis Pro plus the NDMF Mantis wrapper. Mantis without the wrapper → WARN; wrapper without Mantis → FAIL |
| Dependencies | FAIL if an installed package's `vpmDependencies` range isn't met. Ranges like `^`, `~`, `x`, `A - B` and `\|\|` are supported |
| Legacy duplicates | FAIL if an old `.unitypackage` copy listed in `legacyFolders` is still in `Assets/` |
| Backup | WARN if the project has no `.git` |
| Avatar discovery | Lists prefabs and scenes that contain an avatar descriptor **or a variant or instance of one**. It follows `m_SourcePrefab` chains, so prefab variants and scene instances are found too |
| Missing scripts | WARN for script GUIDs that resolve to nothing |

**Checks the script can't make** (use the Unity bridge if there is one, otherwise ask the user):
- The Console has no compile errors. Use `read_console` with type error. Package compile warnings are fine.
- The SDK is signed in, and the avatar has a Blueprint ID if this is an update.
- Whether a Unity bridge exists. If not, offer the setup below or continue in guided-manual mode.

**Gate**
- **Any FAIL:** stop and give the exact fix: which package to add in VCC/ALCOM, "Resolve", "update NDMF", or "delete the legacy folder". Re-run after the fix.
- **Only WARN:** ask before continuing. The user must fix or explicitly accept the backup warning.
- **All PASS:** continue to Phase 1.

## Unity bridge setup: MCP for Unity (Unity 2022.3, which VRChat uses)

Unity's own CLI/MCP needs Unity 6 (`com.unity.pipeline`), so it doesn't work for VRChat projects. Use the community package **MCP for Unity** (CoplayDev), which supports Unity 2021.3 through 6.x. It has been tested with Unity 2022.3.22f1 and v10.2.0.

1. **Prerequisites on the user's PC:** Git for Windows, so Unity can install packages from git URLs, and `uv` (Python 3.10+). On Windows, install uv with `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`. Restart Unity after installing either one.
2. **Add the package (with the user's OK).** Either use Package Manager → Add from git URL `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0`, or add that URL as `"com.coplaydev.unity-mcp"` in `Packages/manifest.json`. Back up `manifest.json` first, to `.avatar-preupload/backup/`. VCC/ALCOM leaves UPM git dependencies alone.
3. **Register the client.** In Unity, open `Window → MCP for Unity`, pick the user's agent (Claude Desktop, Claude Code, Codex, Cursor, …) and click Configure. Use the **stdio** transport for desktop agents.
4. **Restart the agent app completely.** For Claude Desktop, quit it from the system tray; closing the window isn't enough.
5. **Verify.**
   - `~/.unity-mcp/unity-mcp-status-*.json` shows `"reason":"ready"` and the project path.
   - The agent's tool list contains `unityMCP` tools.
   - A `read_console` call succeeds.
   - On Claude's linked-computer sessions, the device info lists `unityMCP` as `announced`. If the tools don't appear, refresh the MCP tool list once.
6. **Screen capture may not help.** It can show a blank or masked Unity window, so diagnose with the status file and the bridge rather than screenshots.

Tools used from MCP for Unity: `execute_code` (runs C# in the Editor, compiled with CodeDom C# 6), `read_console`, `find_gameobjects`, `manage_scene`, and `manage_camera` (screenshots).

## Profile (per avatar)

Store the profile at `<project>/.avatar-preupload/<AvatarName>.profile.yaml`. That folder is outside `Assets/`, so Unity doesn't import it.

```yaml
avatar: "MyAvatar"                    # scene root GameObject name
source: "Assets/Scene.unity (instance of Assets/.../MyAvatar.prefab)"
target: pc                            # pc | mobile | both
mode: quality_first                   # quality_first (default) | rank_target
target_rank: {}                       # only for rank_target, e.g. { pc: Medium, mobile: Medium }
protected:
  renderers: [Body]                   # never simplified, e.g. face mesh with face tracking
  light_reduction_only: []            # e.g. a split-out hands mesh: cap per Phase 3 table
  textures: []                        # never downscale (LAC: Freeze → Skip compression)
  physbones: []
  contacts: []
  features: [face_tracking, expression_menu, outfit_toggles, mmd_compatibility]
removed_for_this_upload: []           # what the user agreed to drop (EditorOnly)
automation:
  configure_safe_optimizers: true
  lac_preset: Balanced                # HighQuality | Quality | Balanced | Aggressive | Maximum
  destructive_mesh_edits: approval_required
  physbone_removal: approval_required
  asset_import_changes: approval_required
  publish: never
```

## Phase 1 — Audit (read-only)

Measure two states:
1. **Original:** the avatar as it is now.
2. **Processed:** what VRChat actually receives after NDMF. Clone the avatar, run `AvatarProcessor.ProcessAvatar(clone)`, measure, then destroy the clone and run `AvatarProcessor.CleanTemporaryAssets()`. This takes about 15 s for a heavy avatar. **The SDK control panel shows pre-NDMF numbers**, so don't judge by it.

**NDMF preview trap:** with NDMF previews enabled, the original avatar in the Scene and Game view already **displays** the simplified or removed meshes. A defect caused by Meshia or AAO therefore also "appears on the original". Never use the scene original as the "before" image. Compare two processed clones instead: one with the current settings, and one with the suspect component or Meshia entry disabled.

The recipes in Appendix B are tested: B1 finds avatars, B2 audits the processed avatar, B3 maps toggles.

**Without a bridge,** ask the user for the **Actual Performance Window** values (anatawa12's Gist Pack) in Play mode, or the in-game Avatar Stats from a previous upload. lilAvatarUtils' Textures tab gives per-texture VRAM.

**Collect:**
- `AvatarPerformanceStats.ToString()` for PC and/or mobile. It gives triangles, skinned meshes, meshes, material slots, bones, PhysBones and their transforms, particles and constraints.
- Contacts, counted as components whose type name starts with `VRCContact`.
- Texture memory from `UnityEditor.TextureUtil.GetStorageMemorySizeLong`, called by reflection.
- **Per renderer: triangles, material names and shaders.** Material slots count once per renderer submesh, so **unique materials per toggle group** decide how far merging can go.
- **What must not break:**
  - Renderers toggled by MA Object Toggle (`referencePath`) or by animation bindings on `m_IsActive` or `m_Enabled`
  - Face-tracking, lip-sync, eye-tracking and MMD BlendShapes
  - Expression parameters and menu items
  - Unresolved animation paths that already exist. Record these as pre-existing so they aren't blamed on the optimization later

**Output:** a table of each metric against the rank limits, showing what rank the avatar lands on, which items set that rank, and which parts cause it.

## Phase 2 — Safe optimizations (if `configure_safe_optimizers: true`)

These only add NDMF components, so removing a component undoes them.
1. **AAO Trace And Optimize** on the avatar root, if it's missing. Keep the defaults. Enable MMD compatibility if that feature is protected. T&O is designed never to change appearance; if it does, remove it and report it as an AAO bug.
2. **LAC Texture Compressor** on the root, with the profile preset. Use Freeze → Skip compression for protected textures, such as face detail, small text or logos, and gradient emission. LAC runs before AAO in the NDMF order automatically.
3. Re-run the processed audit.

## Phase 3 — Approval-required changes (proven techniques)

Present one plan that lists each item's saving, risk and how to undo it, then wait for a yes. In `quality_first` mode, offer only the rows marked **lossless**. Polygon reduction and material swaps are `rank_target` only.

| Goal | Technique (recipe) | Guard |
|---|---|---|
| **Lossless:** drop items the user agreed to remove (props, duplicate variants, toggles turned always-on) | Set `tag = "EditorOnly"` and `SetActive(false)` on the object or menu item (B4). The build strips EditorOnly objects | Remove a whole gimmick at its root so its MA components and Contacts go with it. Removing a toggle's menu item makes the target permanent at its default state. **Before removing, scan for references (B4 does this):** PhysBones that live elsewhere (for example `Armature/PB/<Item>`) and drive only this item should go too. MA Shape Changers on the item (such as a strap that dents the shirt) switch off with it, which is usually what you want |
| **Lossless:** fewer skinned meshes, meshes and material slots | AAO Merge Skinned Mesh on a new child with an empty SMR: always-on SMRs go in `renderersSet`, MeshRenderers in `staticRenderersSet` (B5). Identical materials merge automatically | **Never merge toggled renderers.** Slots after merging = unique materials per toggle group, plus particle slots |
| Last one or two slots (`rank_target` only) | Swap a near-duplicate material on a tiny part, for example DarkSilver → Silver on a ring, by setting `sharedMaterials` on the instance | Show the user. It's purely cosmetic |
| Fewer PhysBones | AAO Merge PhysBone (`makeParent = true`; override differing values such as `maxAngleX` and `maxAngleZ`) (B6) | Only chains with near-identical settings, for example hair bangs |
| **Lossless:** delete hidden body under clothes | AAO Remove Mesh By BlendShape with the body's `Shrink_*` shapes (B7), or Remove Mesh By Box | Only regions confirmed covered from a screenshot. Keep feet with sandals, forearms with short sleeves, and the neckline |
| Triangles (`rank_target` only) | Meshia Cascading Avatar Mesh Simplifier with `AutoAdjustEnabled = false` and per-entry targets (B8). Keep protected renderers and tiny parts `Enabled = false`. Use `PreserveSurfaceCurvature`, plus `PreserveBorderEdges` on hair, clothes and body. Or NDMF Mantis (never Mantis directly) | Stay within the **per-part caps** below. Aim for about 97–99% of the limit, and check every reduced part visually from several angles |
| Protect a region of a shared mesh (for example hands inside the body mesh) | Meshia can't lock part of a mesh. Split the region into its own mesh by bone weights (B10), then give it its own entry (`Enabled = false` or a light target) and add it to Merge Skinned Mesh | Generates two mesh assets under `Assets/_AvatarPreupload/Generated/`; the FBX is untouched. Needs approval. Keep `PreserveBorderEdges` on both halves so the seam doesn't open |
| Mobile (`rank_target` only) | VQT: Tools → VRCQuestTools → Setup Avatar for Mobile → Avatar Converter Settings (Toon Standard, max texture 1024 to start), with PhysBone and Contact pruning | A separate build with its own heavy reduction (aim for mobile Medium). Dynamic Bones must already be PhysBones; Audio Sources and similar get stripped. Mobile hard limits (PB 8, PB transforms 64, colliders 16, collision checks 64, Contacts 16, Constraints 150): exceeding them removes **all** PhysBones/Contacts in-game |
| Shared-asset edits (import Max Size, material cleanup, Missing-component removal) | lilAvatarUtils | List every affected asset |

**Per-part reduction caps (learned from in-game failures; the cut is measured against the processed triangle count before Meshia):**

| Part | Max cut | What broke beyond it |
|---|---|---|
| Face / head mesh with face tracking | 0% (protected) | Expression and lip-sync deformation |
| Hands and fingers | about 30% (e.g. 11,476 → 8,000), and only after splitting them from the body (B10) | A 75% cut on the shared body mesh left fingers badly distorted in-game |
| Skin-tight clothing (shirt, bodysuit, leggings) | about 25% (e.g. 5,328 → 4,100) | A 53% cut let skin poke through the chest at the buttons and pocket |
| Hair cards | test per hair; about 33% (17,888 → 12,000) was clean | A 39% cut opened a hole above the ear. Meshia with `PreserveBorderEdges` may stop above its target, and that stopping point can already be broken. Find the lowest clean target by screenshotting a few candidates |
| Rest of body (arms, legs) | about 50% | — |
| Loose clothing, shoes, bags, belts | about 50% | — |
| Small accessories (chains, crosses, earrings) | up to about 85% | Fine at close range |

If the caps can't reach the rank, tell the user and offer: removing a whole item, accepting PC Very Poor, or relaxing a cap for a part they name.

**Budget method:** list the remaining triangles per renderer and decide the protected ones first, such as the face. Spread the rest so the biggest non-protected parts take the cuts. Heavy accessories, such as chains or crosses with thousands of triangles, are the cheapest wins.

## Phase 4 — Validation

1. Re-run the processed audit against the live limits.
2. Mobile: confirm the hard limits above.
3. Run static checks on a processed clone:
   - toggled renderers still exist separately
   - the face-tracking BlendShape count is unchanged
   - expression parameters are present
   - no new Console errors
   - unresolved animation paths are no worse than in Phase 1
4. **Visual comparison (B9):** take screenshots of a processed clone with `manage_camera` (`view_position`/`view_target`, `output_folder: .avatar-preupload/screenshots`, outside Assets). Take full-body front, back and head close-ups. Use a second processed clone with the change disabled as the "before" (NDMF preview trap). **Destroy the clones and clean temporary assets afterwards.**
5. **Pose test for reduced hands (B11):** curl the fingers into a fist and a point on a processed clone, and compare with a clone whose hands entry is disabled.
6. **Find the culprit of a defect:** make processed clones that each disable one Meshia entry or AAO component (cap it at 1–2 clones per call, see pitfalls), and screenshot the same view. The clone where the defect disappears names the cause.
7. **Checklist for the user:** expressions and face tracking, each toggle, PhysBone motion, hand gestures (fist, point, open), sitting or crouching (hems over deleted legs), and close-ups of reduced hair, hands and tight clothes.
8. **After the user tests in-game:** if they report a defect you can't reproduce, ask for an in-game screenshot plus the gesture, which hand, and the camera angle before guessing.

## Phase 5 — Report

Write the report to `<project>/.avatar-preupload/reports/<YYYY-MM-DD>-<AvatarName>.md` and summarise it in chat. Include:
- Phase 0 result and any warnings the user accepted.
- A before/after table: original, processed at the start, processed at the end, and the limit.
- **A change list with locations and undo steps.**
- Validation results as PASS/WARN/FAIL, plus anything that needs the user's eyes.
- Pre-existing issues you noticed but didn't touch.
- **Upload steps:**
  1. **Press Ctrl+S to save the scene.**
  2. Open SDK → Builder → choose the platforms. For PC plus mobile, use Multi-Platform Build & Publish, uploading PC first or together so PhysBones sync. PC and mobile builds of one avatar get separate ranks.
  3. The SDK panel will still show pre-NDMF ranks, which is expected. If a mobile pre-build check blocks the upload, see https://vpm.anatawa12.com/avatar-optimizer/ja/docs/faq/

End by telling the user the avatar is ready for **them** to upload.

## Pitfalls learned in practice

- The static pre-check only sees components serialized in each file. Inherited ones from base prefabs are invisible, so confirm with the bridge.
- A whole hidden outfit is usually removed by Trace And Optimize. What survives is mostly toggled items and always-on duplicates.
- Duplicate accessories in different places (glasses on face, on head, on a bag) cost a full set of slots and triangles each.
- Shape Changers can target paths that don't exist on this avatar (for example an outfit made for another base). Report these; don't fix them silently.
- In CodeDom C# 6, write `UnityEngine.Object.Instantiate` and `UnityEngine.Object.DestroyImmediate` (`Object` is ambiguous). Find VRChat and tool types by scanning `AppDomain` assemblies, because `Type.GetType` with an assembly name may return null.
- MCP screenshots save to `Assets/Screenshots` by default. Always pass an `output_folder` outside `Assets/`.
- A Unity `Temp/UnityLockfile` means the Editor is open. Editing `manifest.json` is fine because Unity re-resolves on focus.
- **Bridge timeouts:** `ProcessAvatar` takes about 15–20 s on a heavy avatar, and the bridge call times out at about 60 s. Run at most two processed clones per `execute_code` call. If a call times out, Unity may still be working for minutes: wait, then poll with a cheap read-only call. Don't resend the same call. Before telling the user to force-quit, check that the scene file on disk has their latest changes.
- **NDMF preview** makes the scene original look already optimized (see Phase 1). Compare processed clones only.
- `HumanPoseHandler.SetHumanPose` on a clone also moves its body position; re-place the clone by moving its Hips after posing (B11).

## Reference — tools

| Tool | Package ID | Install |
|---|---|---|
| VRChat SDK Avatars / Base | `com.vrchat.avatars`, `com.vrchat.base` | VCC/ALCOM official |
| NDMF | `nadena.dev.ndmf` | Comes with AAO or MA |
| AAO: Avatar Optimizer | `com.anatawa12.avatar-optimizer` | https://vpm.anatawa12.com/avatar-optimizer/ja/#installation |
| LAC: Avatar Compressor | `dev.limitex.avatar-compressor` | VPM repo `https://vpm.limitex.dev/index.json` (needs SDK ≥ 3.10.0, NDMF ≥ 1.10.0) |
| lilAvatarUtils | `jp.lilxyzw.avatar-utils` | VPM repo `https://lilxyzw.github.io/vpm-repos/vpm.json` |
| Meshia Mesh Simplification | `com.ramtype0.meshia.mesh-simplification` | VPM repo `https://RamType0.github.io/VpmRepository/index.json` |
| NDMF Mantis LOD Editor | `.unitypackage` under `Assets/` | https://booth.pm/ja/items/5409262 plus the paid Mantis LOD Editor Pro |
| VRCQuestTools | `com.github.kurotu.vrc-quest-tools` | VPM repo `https://kurotu.github.io/vpm-repos/vpm.json` |
| Modular Avatar | `nadena.dev.modular-avatar` | https://modular-avatar.nadena.dev/ |
| anatawa12's Gist Pack (optional) | `com.anatawa12.gists` | Actual Performance Window |
| MCP for Unity (bridge) | `com.coplaydev.unity-mcp` | git `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.2.0` |

In ALCOM or VCC, add a VPM repo through Settings → Packages → Add Repository, or use `vcc://vpm/addRepo?url=<repo json>`.

## Reference — fallback rank limits (VRChat docs as of 2026-10; prefer live values)

| Metric | PC Excellent | PC Good | PC Medium | PC Poor | Mobile Excellent | Mobile Good | Mobile Medium | Mobile Poor |
|---|---|---|---|---|---|---|---|---|
| Triangles | 32,000 | 70,000 | 70,000 | 70,000 | 7,500 | 10,000 | 15,000 | 20,000 |
| Texture memory | 40 MB | 75 MB | 110 MB | 150 MB | 10 MB | 18 MB | 25 MB | 40 MB |
| Skinned meshes | 1 | 2 | 8 | 16 | 1 | 1 | 2 | 2 |
| Basic meshes | 4 | 8 | 16 | 24 | 1 | 1 | 2 | 2 |
| Material slots | 4 | 8 | 16 | 32 | 1 | 1 | 2 | 4 |
| PhysBone components | 4 | 8 | 16 | 32 | 0 | 4 | 6 | 8 |
| PhysBone transforms | 16 | 64 | 128 | 256 | 0 | 16 | 32 | 64 |
| Contacts | 8 | 16 | 24 | 32 | 2 | 4 | 8 | 16 |
| Bones | 75 | 150 | 256 | 400 | 75 | 90 | 150 | 150 |
| Particle systems | 0 | 4 | 8 | 16 | 0 | 0 | 0 | 2 |

Default "Minimum displayed performance rank": PC = Very Poor (everything is shown); mobile = Medium (Poor and Very Poor are hidden unless the viewer uses Show Avatar).

## Appendix A — precheck.py

Write this verbatim to a temp location (not inside the Unity project) and run it as described in Phase 0.

```python
#!/usr/bin/env python3
"""
avatar-preupload-optimization-check :: Phase 0 project pre-check (read-only).

Reads a VCC / ALCOM managed Unity project from disk WITHOUT opening Unity and
reports whether the packages the optimization workflow depends on are installed,
resolved, version-compatible, and not duplicated by legacy .unitypackage copies.
It also lists files that contain avatars (VRC Avatar Descriptor) and which
optimizer components are already attached in each file.

Usage:
    python3 precheck.py <UnityProjectPath> [--target pc|mobile|both] [--json]
                        [--unity-editor <path to Unity Editor folder>]

Exit code: 0 = all PASS, 1 = WARN only, 2 = at least one FAIL.
Stdlib only. Never writes to the project.
"""
import argparse
import json
import os
import re
import sys

# --------------------------------------------------------------------------- #
# Package catalogue
# --------------------------------------------------------------------------- #
# level: required | required-mobile | recommended | optional
PACKAGES = [
    ("com.vrchat.base", "VRChat SDK - Base", "required", "VRChat SDK core"),
    ("com.vrchat.avatars", "VRChat SDK - Avatars", "required", "Avatar upload + performance stats"),
    ("nadena.dev.ndmf", "NDMF", "required", "Non-destructive build pipeline used by AAO / LAC / Meshia / VQT"),
    ("com.anatawa12.avatar-optimizer", "AAO: Avatar Optimizer", "required",
     "Trace And Optimize, Merge Skinned Mesh, Remove Mesh By Box/BlendShape"),
    ("dev.limitex.avatar-compressor", "LAC: Avatar Compressor", "recommended",
     "LAC Texture Compressor (complexity-aware texture compression)"),
    ("jp.lilxyzw.avatar-utils", "lilAvatarUtils", "recommended",
     "Inspect heavy textures / PhysBones, clean materials, remove Missing components"),
    ("com.ramtype0.meshia.mesh-simplification", "Meshia Mesh Simplification", "recommended",
     "Polygon reduction (free alternative to Mantis LOD Editor)"),
    ("com.github.kurotu.vrc-quest-tools", "VRCQuestTools", "required-mobile",
     "Android / iOS conversion, PhysBone / Contact pruning"),
    ("nadena.dev.modular-avatar", "Modular Avatar", "optional", "MA Mesh Settings, outfit setup"),
    ("com.anatawa12.gists", "anatawa12's Gist Pack", "optional",
     "Actual Performance Window (post-NDMF performance rank)"),
    ("jp.lilxyzw.liltoon", "lilToon", "optional", "Shader; AAO texture optimisation supports it"),
]

VCC_ADD_HINT = {
    "com.anatawa12.avatar-optimizer": "https://vpm.anatawa12.com/avatar-optimizer/ja/#installation",
    "dev.limitex.avatar-compressor": "https://lac.limitex.dev/ja/docs/installation/",
    "jp.lilxyzw.avatar-utils": "VCC repo https://lilxyzw.github.io/vpm-repos/vpm.json",
    "com.ramtype0.meshia.mesh-simplification": "https://ramtype0.github.io/VpmRepository/",
    "com.github.kurotu.vrc-quest-tools": "https://kurotu.github.io/vpm-repos/vpm.html",
    "nadena.dev.modular-avatar": "https://modular-avatar.nadena.dev/",
    "nadena.dev.ndmf": "installed automatically with AAO / Modular Avatar",
    "com.anatawa12.gists": "https://vpm.anatawa12.com/gists/",
}

# Keywords matched against attached component script file names.
OPTIMIZER_COMPONENTS = [
    ("TraceAndOptimize", "AAO Trace And Optimize"),
    ("MergeSkinnedMesh", "AAO Merge Skinned Mesh"),
    ("RemoveMeshInBox", "AAO Remove Mesh By Box"),
    ("RemoveMeshByBox", "AAO Remove Mesh By Box"),
    ("RemoveMeshByBlendShape", "AAO Remove Mesh By BlendShape"),
    ("MergePhysBone", "AAO Merge PhysBone"),
    ("MergeBone", "AAO Merge Bone"),
    ("TextureCompressor", "LAC Texture Compressor"),
    ("CascadingAvatarMeshSimplifier", "Meshia Cascading Avatar Mesh Simplifier"),
    ("MeshiaMeshSimplifier", "Meshia Mesh Simplifier"),
    ("MantisLodEditor", "NDMF Mantis LOD Editor"),
    ("AvatarConverterSettings", "VQT Avatar Converter Settings"),
    ("MeshSettings", "MA Mesh Settings"),
]

UNITY_BUILTIN_GUIDS = {
    "0000000000000000e000000000000000",
    "0000000000000000f000000000000000",
    "0000000000000000d000000000000000",
}

# --------------------------------------------------------------------------- #
# Minimal semver range evaluation (enough for VPM dependency strings)
# --------------------------------------------------------------------------- #
VERSION_RE = re.compile(r"^v?(\d+|[xX*])(?:\.(\d+|[xX*]))?(?:\.(\d+|[xX*]))?(?:-([0-9A-Za-z.-]+))?(?:\+.*)?$")


def parse_version(s):
    m = VERSION_RE.match(s.strip())
    if not m:
        return None
    parts = [m.group(1), m.group(2), m.group(3)]
    nums = []
    for p in parts:
        if p is None or p in ("x", "X", "*"):
            nums.append(None)
        else:
            nums.append(int(p))
    return nums, m.group(4)


def _pre_key(pre):
    if pre is None:
        return (1,)  # release sorts after any prerelease
    out = []
    for ident in pre.split("."):
        out.append((0, int(ident), "") if ident.isdigit() else (1, 0, ident))
    return (0, tuple(out))


def vkey(nums, pre):
    return (tuple(n or 0 for n in nums), _pre_key(pre))


def _bounds(op, nums, pre):
    """Return list of (op, key) constraints for one comparator."""
    filled = [n for n in nums if n is not None]
    if op == "^":
        lo = vkey(nums, pre)
        maj, mnr, pat = (nums + [0, 0, 0])[:3]
        maj, mnr, pat = maj or 0, mnr or 0, pat or 0
        if maj > 0:
            hi = ((maj + 1, 0, 0), _pre_key("0"))
        elif mnr > 0:
            hi = ((0, mnr + 1, 0), _pre_key("0"))
        else:
            hi = ((0, 0, pat + 1), _pre_key("0"))
        return [(">=", lo), ("<", hi)]
    if op == "~":
        lo = vkey(nums, pre)
        maj = nums[0] or 0
        mnr = nums[1]
        hi = ((maj, mnr + 1, 0), _pre_key("0")) if mnr is not None else ((maj + 1, 0, 0), _pre_key("0"))
        return [(">=", lo), ("<", hi)]
    if op in ("", "=") and len(filled) < 3:
        # wildcard / partial: 3.5.x, 3.5, 3.x
        if not filled:
            return []
        lo = (tuple((filled + [0, 0, 0])[:3]), _pre_key("0"))
        up = list(filled)
        up[-1] += 1
        hi = (tuple((up + [0, 0, 0])[:3]), _pre_key("0"))
        return [(">=", lo), ("<", hi)]
    key = vkey(nums, pre)
    return [(op or "=", key)]


def satisfies(version, rng):
    pv = parse_version(version)
    if pv is None:
        return None
    v = vkey(*pv)
    rng = (rng or "").strip()
    if rng in ("", "*", "x", "latest"):
        return True
    for alt in rng.split("||"):
        ok = True
        hy = re.match(r"^\s*(\S+)\s+-\s+(\S+)\s*$", alt)  # hyphen range "A - B"
        if hy:
            lo, hi = parse_version(hy.group(1)), parse_version(hy.group(2))
            if lo is None or hi is None:
                return None
            if v < (tuple((n or 0) for n in lo[0]), _pre_key(lo[1])):
                ok = False
            if any(n is None for n in hi[0]):  # partial upper bound: "3.10" means < 3.11.0
                if not v < _bounds("", *hi)[1][1]:
                    ok = False
            elif not v <= vkey(*hi):
                ok = False
            if ok:
                return True
            continue
        for tok in re.findall(r"(>=|<=|>|<|=|\^|~)?\s*([0-9A-Za-z.*+-]+)", alt):
            op, ver = tok
            pr = parse_version(ver)
            if pr is None:
                return None
            for cop, ck in _bounds(op, *pr):
                if cop == ">=" and not v >= ck: ok = False
                elif cop == ">" and not v > ck: ok = False
                elif cop == "<=" and not v <= ck: ok = False
                elif cop == "<" and not v < ck: ok = False
                elif cop == "=" and not v == ck: ok = False
        if ok:
            return True
    return False


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self):
        self.items = []

    def add(self, status, check, detail, fix=None):
        self.items.append({"status": status, "check": check, "detail": detail, "fix": fix})

    @property
    def worst(self):
        s = {i["status"] for i in self.items}
        return "FAIL" if "FAIL" in s else "WARN" if "WARN" in s else "PASS"


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


GUID_RE = re.compile(r"^guid:\s*([0-9a-f]{32})", re.M)
SCRIPT_RE = re.compile(r"m_Script:\s*\{fileID:\s*(-?\d+),\s*guid:\s*([0-9a-f]{32})")
SOURCE_PREFAB_RE = re.compile(r"m_SourcePrefab:\s*\{fileID:\s*-?\d+,\s*guid:\s*([0-9a-f]{32})")


def build_meta_index(roots):
    """guid -> asset path (asset path = meta path without .meta)."""
    index = {}
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if not d.startswith(".")]
            for fn in fns:
                if not fn.endswith(".meta"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    with open(p, encoding="utf-8", errors="ignore") as f:
                        head = f.read(400)
                except OSError:
                    continue
                m = GUID_RE.search(head)
                if m:
                    index[m.group(1)] = p[:-5]
    return index


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
def check_project(proj, target, unity_editor, rep):
    pk = os.path.join(proj, "Packages")
    vpm_path = os.path.join(pk, "vpm-manifest.json")
    vpm = read_json(vpm_path)
    if vpm is None:
        rep.add("FAIL", "Project type",
                "Packages/vpm-manifest.json not found or unreadable: this is not a VCC / ALCOM managed project "
                "(or the path is not the Unity project root).",
                "Open/migrate the project with VCC or ALCOM. Legacy .unitypackage SDK projects are not supported.")
        return {}
    rep.add("PASS", "Project type", "VCC / ALCOM managed project (Packages/vpm-manifest.json found).")

    # Unity version
    pv = os.path.join(proj, "ProjectSettings", "ProjectVersion.txt")
    unity_ver = None
    try:
        with open(pv, encoding="utf-8") as f:
            m = re.search(r"m_EditorVersion:\s*(\S+)", f.read())
            unity_ver = m.group(1) if m else None
    except OSError:
        pass
    if unity_ver is None:
        rep.add("WARN", "Unity version", "ProjectSettings/ProjectVersion.txt not readable.")
    elif unity_ver.startswith("2022.3."):
        rep.add("PASS", "Unity version", f"Unity {unity_ver}.")
    else:
        rep.add("WARN", "Unity version",
                f"Unity {unity_ver}. VRChat avatar projects normally use the Unity 2022.3 LTS build VRChat specifies.",
                "Confirm against VRChat's currently supported Unity version before uploading.")

    # Installed embedded packages
    installed = {}
    if os.path.isdir(pk):
        for d in sorted(os.listdir(pk)):
            pj = read_json(os.path.join(pk, d, "package.json"))
            if pj and pj.get("name"):
                installed[pj["name"]] = {"version": pj.get("version", "?"), "dir": d, "pkg": pj}

    # UPM manifest (git / registry packages)
    upm = read_json(os.path.join(pk, "manifest.json")) or {}
    upm_deps = upm.get("dependencies", {}) or {}
    upm_lock = (read_json(os.path.join(pk, "packages-lock.json")) or {}).get("dependencies", {})
    for name, spec in upm_deps.items():
        if name not in installed:
            ver = (upm_lock.get(name) or {}).get("version", spec)
            installed[name] = {"version": ver, "dir": None, "pkg": None, "upm": True}

    # vpm-manifest vs Packages folder (what the VCC Resolver compares)
    wanted = {}
    for sect in ("locked", "dependencies"):
        for name, info in (vpm.get(sect) or {}).items():
            ver = info.get("version") if isinstance(info, dict) else info
            wanted.setdefault(name, ver)
    unresolved = [n for n in wanted if n not in installed]
    if unresolved:
        rep.add("FAIL", "Packages resolved",
                "Listed in vpm-manifest.json but missing from Packages/: " + ", ".join(sorted(unresolved)),
                "Open the project in VCC / ALCOM (or click Resolve in the VRChat SDK Resolver) and restore packages.")
    else:
        rep.add("PASS", "Packages resolved", f"All {len(wanted)} VPM packages in vpm-manifest.json are present.")
    for name, ver in wanted.items():
        inst = installed.get(name)
        if inst and ver and inst["version"] != ver and satisfies(inst["version"], ver) is False:
            rep.add("WARN", "Package version drift",
                    f"{name}: manifest locks {ver}, folder has {inst['version']}.",
                    "Re-resolve in VCC / ALCOM.")

    # Required / recommended catalogue
    meshia_or_mantis = None
    for pid, label, level, purpose in PACKAGES:
        inst = installed.get(pid)
        need = level == "required" or (level == "required-mobile" and target in ("mobile", "both"))
        if inst:
            rep.add("PASS", f"Package: {label}", f"{pid} {inst['version']} — {purpose}")
            continue
        hint = VCC_ADD_HINT.get(pid)
        if pid == "com.ramtype0.meshia.mesh-simplification":
            meshia_or_mantis = "missing"
            continue  # decided after Mantis scan
        if need:
            rep.add("FAIL", f"Package: {label}", f"{pid} not installed — {purpose}",
                    f"Add with VCC / ALCOM ({hint})." if hint else "Add with VCC / ALCOM.")
        elif level in ("recommended", "required-mobile"):
            rep.add("WARN", f"Package: {label}", f"{pid} not installed — {purpose}",
                    f"Add with VCC / ALCOM ({hint})." if hint else None)
        else:
            rep.add("INFO", f"Package: {label}", f"{pid} not installed (optional) — {purpose}")

    # Mantis (Asset Store + BOOTH unitypackage, lives under Assets/)
    mantis_core, mantis_ndmf = [], []
    assets = os.path.join(proj, "Assets")
    if os.path.isdir(assets):
        for dp, dns, fns in os.walk(assets):
            dns[:] = [d for d in dns if not d.startswith(".")]
            for n in dns + fns:
                low = n.lower()
                if "mantis" in low and not low.endswith(".meta"):
                    rel = os.path.relpath(os.path.join(dp, n), proj)
                    (mantis_ndmf if "ndmf" in low else mantis_core).append(rel)
    if meshia_or_mantis == "missing":
        if mantis_core and mantis_ndmf:
            rep.add("PASS", "Polygon reduction tool",
                    "Meshia not installed, but Mantis LOD Editor + NDMF Mantis LOD Editor found under Assets/.")
        elif mantis_core and not mantis_ndmf:
            rep.add("WARN", "Polygon reduction tool",
                    "Mantis LOD Editor found but the NDMF wrapper is missing; using Mantis directly edits the FBX mesh.",
                    "Install NDMF Mantis LOD Editor (https://booth.pm/ja/items/5409262) or Meshia "
                    "(https://ramtype0.github.io/VpmRepository/).")
        elif mantis_ndmf and not mantis_core:
            rep.add("FAIL", "Polygon reduction tool",
                    "NDMF Mantis LOD Editor found but Mantis LOD Editor Professional (paid) is missing.",
                    "Import Mantis LOD Editor Professional, or switch to Meshia.")
        else:
            rep.add("WARN", "Polygon reduction tool",
                    "Neither Meshia nor Mantis LOD Editor is installed; polygon reduction step will be skipped.",
                    "Add Meshia with VCC / ALCOM (https://ramtype0.github.io/VpmRepository/).")

    # Dependency satisfaction declared by each installed package
    for name, inst in sorted(installed.items()):
        pj = inst.get("pkg") or {}
        for dep, rng in (pj.get("vpmDependencies") or {}).items():
            have = installed.get(dep)
            if not have:
                rep.add("FAIL", "Dependency", f"{name} needs {dep} {rng}, which is not installed.",
                        "Resolve / add it in VCC / ALCOM.")
                continue
            ok = satisfies(have["version"], rng)
            if ok is False:
                rep.add("FAIL", "Dependency",
                        f"{name} {inst['version']} needs {dep} {rng}, but {have['version']} is installed.",
                        f"Update {dep} (or {name}) in VCC / ALCOM so the versions match.")
            elif ok is None:
                rep.add("WARN", "Dependency", f"Could not evaluate '{rng}' for {dep} {have['version']} ({name}).")

    # Legacy duplicates (.unitypackage copies left in Assets/)
    for name, inst in installed.items():
        pj = inst.get("pkg") or {}
        for folder in (pj.get("legacyFolders") or {}):
            if os.path.isdir(os.path.join(proj, folder.replace("\\", os.sep))):
                rep.add("FAIL", "Legacy duplicate",
                        f"{name} is installed via VPM but legacy folder '{folder}' still exists.",
                        "Remove the legacy folder (VCC 'Resolve' can do it) to avoid duplicate scripts / compile errors.")
        for lf in (pj.get("legacyFiles") or {}):
            if os.path.isfile(os.path.join(proj, lf.replace("\\", os.sep))):
                rep.add("WARN", "Legacy duplicate", f"{name}: legacy file '{lf}' still exists.")

    # Android / iOS build support (only if we can see the editor install)
    if target in ("mobile", "both"):
        if unity_editor:
            pe = os.path.join(unity_editor, "Data", "PlaybackEngines")
            if not os.path.isdir(pe):
                pe = os.path.join(unity_editor, "PlaybackEngines")
            if os.path.isdir(os.path.join(pe, "AndroidPlayer")):
                rep.add("PASS", "Android Build Support", "AndroidPlayer module found in the Unity editor install.")
            else:
                rep.add("FAIL", "Android Build Support", f"AndroidPlayer module not found under {pe}.",
                        "Unity Hub → Installs → (editor) → Add modules → Android Build Support.")
        else:
            rep.add("INFO", "Android Build Support",
                    "Not verified (editor install not given). Mobile upload needs Android Build Support "
                    "(+ iOS Build Support for iOS).",
                    "Check Unity Hub → Installs, or re-run with --unity-editor.")

    # Backup / version control
    if os.path.isdir(os.path.join(proj, ".git")):
        rep.add("PASS", "Backup", "Project is under git; commit before optimizing so every change is reversible.")
    else:
        rep.add("WARN", "Backup", "No git repository found in the project.",
                "Make a backup (VCC / ALCOM 'Make Backup', or copy the project) before any optimization step.")

    return installed


def scan_avatars(proj, rep):
    assets = os.path.join(proj, "Assets")
    meta_roots = [assets, os.path.join(proj, "Packages"), os.path.join(proj, "Library", "PackageCache")]
    have_cache = os.path.isdir(os.path.join(proj, "Library", "PackageCache"))
    index = build_meta_index(meta_roots)
    path_to_guid = {v: k for k, v in index.items()}
    files = {}  # abs path -> scan info
    for dp, dns, fns in os.walk(assets):
        dns[:] = [d for d in dns if not d.startswith(".")]
        for fn in fns:
            if not fn.endswith((".unity", ".prefab")):
                continue
            p = os.path.join(dp, fn)
            info = {"descriptors": 0, "names": set(), "missing": set(), "sources": {}}
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    head = f.read(64)
                    if not head.startswith("%YAML"):
                        continue  # binary-serialized asset: skip
                    f.seek(0)
                    for line in f:
                        if "customizeAnimationLayers:" in line:
                            info["descriptors"] += 1
                        s = SOURCE_PREFAB_RE.search(line)
                        if s:
                            g = s.group(1)
                            info["sources"][g] = info["sources"].get(g, 0) + 1
                        m = SCRIPT_RE.search(line)
                        if m:
                            guid = m.group(2)
                            if guid in UNITY_BUILTIN_GUIDS:
                                continue
                            path = index.get(guid)
                            if path:
                                info["names"].add(os.path.splitext(os.path.basename(path))[0])
                            elif have_cache:
                                info["missing"].add(guid)
            except OSError:
                continue
            files[p] = info

    # Prefab variants and prefab instances (in scenes or other prefabs) do not re-serialize the
    # avatar descriptor; follow m_SourcePrefab chains back to a prefab that has one (fixpoint).
    avatar_guids = {path_to_guid.get(p) for p, i in files.items() if i["descriptors"]} - {None}
    via = {}  # file -> set of avatar prefab files it instantiates
    changed = True
    while changed:
        changed = False
        for p, i in files.items():
            hits = [g for g in i["sources"] if g in avatar_guids]
            if not hits:
                continue
            via.setdefault(p, set()).update(os.path.relpath(index[g], proj) for g in hits if g in index)
            g_self = path_to_guid.get(p)
            if g_self and g_self not in avatar_guids and p.endswith(".prefab"):
                avatar_guids.add(g_self)
                changed = True

    found = []
    for p, i in sorted(files.items()):
        instances = sum(n for g, n in i["sources"].items() if g in avatar_guids)
        if not i["descriptors"] and not instances:
            continue
        comps = sorted({label for key, label in OPTIMIZER_COMPONENTS
                        for n in i["names"] if key.lower() in n.lower()})
        found.append({
            "file": os.path.relpath(p, proj),
            "avatar_descriptors": i["descriptors"],
            "avatar_prefab_instances": instances,
            "instance_of": sorted(via.get(p, [])),
            "optimizer_components": comps,
            "unresolved_script_guids": sorted(i["missing"]),
        })
    if not found:
        rep.add("WARN", "Avatar discovery", "No scene/prefab with a VRC Avatar Descriptor found under Assets/.",
                "Check the project path, or the avatar may be in a binary-serialized asset.")
    else:
        n_desc = sum(a["avatar_descriptors"] for a in found)
        n_inst = sum(a["avatar_prefab_instances"] for a in found)
        rep.add("PASS", "Avatar discovery",
                f"{n_desc} avatar descriptor(s) + {n_inst} avatar prefab variant/instance(s) in {len(found)} file(s). "
                "Static scan only: components shown are those serialized in each file (inherited ones are not); "
                "confirm in Unity when a bridge is available.")
        for a in found:
            if a["unresolved_script_guids"]:
                rep.add("WARN", "Missing scripts",
                        f"{a['file']}: {len(a['unresolved_script_guids'])} component script(s) not found in project "
                        "(possible Missing components / missing package).",
                        "Open in Unity and check for 'Missing (Mono Script)'; lilAvatarUtils → Tools → "
                        "'Remove Missing components' after confirming nothing is needed.")
    if not have_cache:
        rep.add("INFO", "Missing scripts",
                "Library/PackageCache not present (project never opened on this machine?): missing-script check skipped.")
    return found


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--target", choices=["pc", "mobile", "both"], default="pc")
    ap.add_argument("--unity-editor", help="Unity Editor folder, e.g. .../Hub/Editor/2022.3.22f1/Editor")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    proj = os.path.abspath(a.project)
    rep = Report()
    installed = check_project(proj, a.target, a.unity_editor, rep)
    avatars = scan_avatars(proj, rep) if installed else []

    if a.json:
        print(json.dumps({
            "project": proj, "target": a.target, "overall": rep.worst,
            "checks": rep.items,
            "installed_packages": {k: v["version"] for k, v in sorted(installed.items())},
            "avatars": avatars,
        }, ensure_ascii=False, indent=2))
    else:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌", "INFO": "ℹ️ "}
        print(f"Avatar pre-upload pre-check — {proj}  (target: {a.target})")
        print("=" * 72)
        for i in rep.items:
            print(f"{icon[i['status']]} [{i['status']}] {i['check']}: {i['detail']}")
            if i["fix"] and i["status"] != "PASS":
                print(f"      → {i['fix']}")
        if avatars:
            print("\nAvatars found:")
            for av in avatars:
                comps = ", ".join(av["optimizer_components"]) or "(none serialized in this file)"
                kind = []
                if av["avatar_descriptors"]:
                    kind.append(f"{av['avatar_descriptors']} descriptor(s)")
                if av["avatar_prefab_instances"]:
                    kind.append(f"{av['avatar_prefab_instances']} instance(s) of " + ", ".join(av["instance_of"]))
                print(f"  - {av['file']}  [{'; '.join(kind)}]  optimizers: {comps}")
        print("=" * 72)
        print(f"OVERALL: {rep.worst}")
    sys.exit({"PASS": 0, "WARN": 1, "FAIL": 2}[rep.worst])


if __name__ == "__main__":
    main()
```

## Appendix B — Unity bridge recipes (C# for MCP for Unity `execute_code`)

These are method bodies; `return` sends the result back. They compile with CodeDom C# 6 and were tested on Unity 2022.3.22f1 with VRChat SDK 3.10.5, NDMF 1.14.8, AAO 1.9.20, MA 1.18.7 and Meshia 3.2.0. Every recipe begins with the same two lines. Set `AVATAR` to the avatar's scene root name. Keep each call to at most two `ProcessAvatar` runs (bridge timeout).

```csharp
string AVATAR = "MyAvatar";
System.Func<string, System.Type> T = n => { foreach (var a in System.AppDomain.CurrentDomain.GetAssemblies()) { var x = a.GetType(n); if (x != null) return x; } return null; };
```

When a type or field name differs in another version, list the fields by adding the component to a hidden temporary GameObject and walking `new SerializedObject(c).GetIterator()` with `NextVisible`. Then adapt.

### B1 — List avatars in open scenes (read-only)
```csharp
var sb = new System.Text.StringBuilder();
var dt = T("VRC.SDK3.Avatars.Components.VRCAvatarDescriptor");
foreach (var d in Resources.FindObjectsOfTypeAll(dt)) {
  var c = (Component)d; if (EditorUtility.IsPersistent(c)) continue;
  var go = c.gameObject; var src = PrefabUtility.GetCorrespondingObjectFromSource(go); int tris = 0;
  foreach (var r in go.GetComponentsInChildren<SkinnedMeshRenderer>(true)) if (r.sharedMesh != null) tris += r.sharedMesh.triangles.Length / 3;
  sb.AppendLine(go.name + " | active=" + go.activeInHierarchy + " | prefab=" + (src != null ? AssetDatabase.GetAssetPath(src) : "-") + " | rawSkinnedTris=" + tris);
}
return sb.ToString();
```

### B2 — Processed audit: stats, texture memory, renderers and materials (read-only; uses a temporary clone)
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
if (av == null) return "avatar not found";
bool MOBILE = false; var sb = new System.Text.StringBuilder();
var clone = UnityEngine.Object.Instantiate(av); clone.name = "PREUPLOAD_AUDIT_CLONE";
try {
  nadena.dev.ndmf.AvatarProcessor.ProcessAvatar(clone);
  VRC.SDKBase.Validation.Performance.Stats.AvatarPerformanceStats.Initialize();
  var s = new VRC.SDKBase.Validation.Performance.Stats.AvatarPerformanceStats(MOBILE);
  VRC.SDKBase.Validation.Performance.AvatarPerformance.CalculatePerformanceStats(clone.name, clone, s, MOBILE);
  sb.AppendLine(s.ToString());
  int contacts = 0; foreach (var c in clone.GetComponentsInChildren<Component>(true)) if (c != null && c.GetType().Name.StartsWith("VRCContact")) contacts++;
  sb.AppendLine("Contacts: " + contacts);
  var mem = typeof(Editor).Assembly.GetType("UnityEditor.TextureUtil").GetMethod("GetStorageMemorySizeLong", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
  var seen = new System.Collections.Generic.HashSet<Texture>(); long tex = 0;
  foreach (var r in clone.GetComponentsInChildren<Renderer>(true)) foreach (var m in r.sharedMaterials) { if (m == null) continue; foreach (var pn in m.GetTexturePropertyNames()) { var t = m.GetTexture(pn); if (t != null && seen.Add(t)) tex += (long)mem.Invoke(null, new object[]{ t }); } }
  sb.AppendLine("Texture memory ~" + (tex / 1048576.0).ToString("0.0") + " MB");
  foreach (var r in clone.GetComponentsInChildren<Renderer>(true)) {
    var smr = r as SkinnedMeshRenderer; var mf = r.GetComponent<MeshFilter>(); Mesh mesh = smr != null ? smr.sharedMesh : (mf != null ? mf.sharedMesh : null);
    var names = new System.Collections.Generic.List<string>(); foreach (var m in r.sharedMaterials) names.Add(m == null ? "null" : m.name + "{" + m.shader.name + "}");
    sb.AppendLine((mesh != null ? mesh.triangles.Length / 3 : 0) + " | " + AnimationUtility.CalculateTransformPath(r.transform, clone.transform) + " :: " + string.Join(", ", names.ToArray()) + (mesh != null && smr != null ? " | blendshapes=" + mesh.blendShapeCount : ""));
  }
} catch (System.Exception e) { sb.AppendLine("ERROR " + e); }
finally { UnityEngine.Object.DestroyImmediate(clone); nadena.dev.ndmf.AvatarProcessor.CleanTemporaryAssets(); }
return sb.ToString();
```
For the original (unprocessed) stats, run the same `CalculatePerformanceStats` call on `av` without cloning. For per-renderer numbers before AAO merges them, destroy the Merge Skinned Mesh components on the clone before processing (Trace And Optimize may still auto-merge some).

### B3 — Toggle and protection map (read-only)
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var sb = new System.Text.StringBuilder();
foreach (var c in av.GetComponentsInChildren<MonoBehaviour>(true)) {
  if (c == null) continue; var tn = c.GetType().Name;
  if (tn != "ModularAvatarObjectToggle" && tn != "ModularAvatarMenuItem" && tn != "ModularAvatarShapeChanger") continue;
  var it = new SerializedObject(c).GetIterator(); var refs = new System.Collections.Generic.List<string>();
  while (it.Next(true)) if (it.propertyType == SerializedPropertyType.String && (it.name == "referencePath" || it.name == "ShapeName")) refs.Add(it.stringValue);
  sb.AppendLine(tn + " @ " + AnimationUtility.CalculateTransformPath(c.transform, av.transform) + " -> " + string.Join(", ", refs.ToArray()));
}
var clips = new System.Collections.Generic.HashSet<AnimationClip>();
foreach (var c in av.GetComponentsInChildren<MonoBehaviour>(true)) if (c != null && c.GetType().Name == "ModularAvatarMergeAnimator") { var rac = new SerializedObject(c).FindProperty("animator").objectReferenceValue as RuntimeAnimatorController; if (rac != null) foreach (var cl in rac.animationClips) clips.Add(cl); }
var layers = new SerializedObject(av.GetComponent(T("VRC.SDK3.Avatars.Components.VRCAvatarDescriptor"))).FindProperty("baseAnimationLayers");
for (int i = 0; i < layers.arraySize; i++) { var rac = layers.GetArrayElementAtIndex(i).FindPropertyRelative("animatorController").objectReferenceValue as RuntimeAnimatorController; if (rac != null) foreach (var cl in rac.animationClips) clips.Add(cl); }
var toggled = new System.Collections.Generic.SortedSet<string>();
foreach (var cl in clips) foreach (var b in AnimationUtility.GetCurveBindings(cl)) if (b.propertyName == "m_IsActive" || b.propertyName == "m_Enabled") toggled.Add(b.path + " (" + b.propertyName + ")");
sb.AppendLine(clips.Count + " clips; animated on/off: " + string.Join("; ", new System.Collections.Generic.List<string>(toggled).ToArray()));
return sb.ToString();
```

### B4 — Remove objects or menu items from this upload (EditorOnly, undoable), with a reference scan
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var paths = new[]{ "SomeGimmickRoot", "Outfit/Menu/Item_OFF" };   // relative to the avatar root
bool APPLY = false;                                                 // first run false: report references only
Undo.SetCurrentGroupName("Preupload: EditorOnly"); var sb = new System.Text.StringBuilder();
var targets = new System.Collections.Generic.List<GameObject>();
foreach (var p in paths) { var t = av.transform.Find(p); if (t == null) { sb.AppendLine("MISSING " + p); continue; } targets.Add(t.gameObject); }
var names = new System.Collections.Generic.HashSet<string>(); foreach (var g in targets) names.Add(g.name);
foreach (var c in av.GetComponentsInChildren<MonoBehaviour>(true)) { if (c == null) continue; var it = new SerializedObject(c).GetIterator();
  while (it.Next(true)) { bool hit = false;
    if (it.propertyType == SerializedPropertyType.String && it.name == "referencePath") foreach (var n in names) if (it.stringValue.EndsWith("/" + n) || it.stringValue == n) hit = true;
    if (it.propertyType == SerializedPropertyType.ObjectReference && it.objectReferenceValue != null && it.name != "m_CorrespondingSourceObject" && names.Contains(it.objectReferenceValue.name)) hit = true;
    if (hit) { sb.AppendLine("referenced by " + c.GetType().Name + " @ " + AnimationUtility.CalculateTransformPath(c.transform, av.transform) + " (" + it.propertyPath + ")"); break; } } }
// PhysBones whose root sits under an item's own bones (e.g. Armature/Hips/Spine/<Item>) are listed by name match too
foreach (Component pb in av.GetComponentsInChildren(T("VRC.SDK3.Dynamics.PhysBone.Components.VRCPhysBone"), true)) { var root = new SerializedObject(pb).FindProperty("rootTransform").objectReferenceValue as Transform; if (root == null) root = pb.transform;
  foreach (var n in names) if (AnimationUtility.CalculateTransformPath(root, av.transform).Contains("/" + n)) sb.AppendLine("PhysBone for item: " + AnimationUtility.CalculateTransformPath(pb.transform, av.transform) + " root=" + root.name); }
if (APPLY) foreach (var g in targets) { Undo.RecordObject(g, "EditorOnly"); g.tag = "EditorOnly"; g.SetActive(false); PrefabUtility.RecordPrefabInstancePropertyModifications(g); sb.AppendLine("removed " + g.name); }
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(av.scene);
return sb.ToString();
```
Before adding a PhysBone holder (such as `Armature/PB/Bag`) to `paths`, confirm that no active skinned mesh is weighted to the bones its PhysBones drive. References from Merge Skinned Mesh and Meshia entries are harmless, because a removed renderer is simply skipped.

### B5 — AAO Merge Skinned Mesh for every always-on renderer
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var exclude = new System.Collections.Generic.HashSet<string>{ "Glasses_Eyes" };   // toggled renderers (from B3)
var skinned = new System.Collections.Generic.List<SkinnedMeshRenderer>(); var statics = new System.Collections.Generic.List<MeshRenderer>();
foreach (var r in av.GetComponentsInChildren<SkinnedMeshRenderer>(false)) if (r.enabled && r.sharedMesh != null && !exclude.Contains(r.name)) skinned.Add(r);
foreach (var r in av.GetComponentsInChildren<MeshRenderer>(false)) if (r.enabled && !exclude.Contains(r.name)) statics.Add(r);
var obj = new GameObject("PreuploadMergedMain"); Undo.RegisterCreatedObjectUndo(obj, "merge"); obj.transform.SetParent(av.transform, false);
var smr = obj.AddComponent<SkinnedMeshRenderer>(); var anchorSrc = skinned.Count > 0 ? skinned[0] : null;
if (anchorSrc != null) { smr.rootBone = anchorSrc.rootBone; smr.probeAnchor = anchorSrc.probeAnchor; }
var so = new SerializedObject(obj.AddComponent(T("Anatawa12.AvatarOptimizer.MergeSkinnedMesh")));
var a1 = so.FindProperty("renderersSet.mainSet"); a1.arraySize = skinned.Count; for (int i = 0; i < skinned.Count; i++) a1.GetArrayElementAtIndex(i).objectReferenceValue = skinned[i];
var a2 = so.FindProperty("staticRenderersSet.mainSet"); a2.arraySize = statics.Count; for (int i = 0; i < statics.Count; i++) a2.GetArrayElementAtIndex(i).objectReferenceValue = statics[i];
so.FindProperty("removeEmptyRendererObject").boolValue = true; so.ApplyModifiedProperties();
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(av.scene);
return "merged " + skinned.Count + " skinned + " + statics.Count + " static";
```
`doNotMergeMaterials` is empty by default, so identical materials share one slot.

### B6 — AAO Merge PhysBone (for example hair bangs whose roots' parents start with "bang")
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var pbs = new System.Collections.Generic.List<Component>(); Transform commonParent = null;
foreach (Component pb in av.GetComponentsInChildren(T("VRC.SDK3.Dynamics.PhysBone.Components.VRCPhysBone"), true)) {
  var root = new SerializedObject(pb).FindProperty("rootTransform").objectReferenceValue as Transform; if (root == null) root = pb.transform;
  if (root.parent != null && root.parent.name.StartsWith("bang")) { pbs.Add(pb); commonParent = root.parent.parent; } }
if (pbs.Count < 2) return "nothing to merge";
var obj = new GameObject("PreuploadMergePB"); Undo.RegisterCreatedObjectUndo(obj, "merge pb"); obj.transform.SetParent(commonParent, false);
var so = new SerializedObject(obj.AddComponent(T("Anatawa12.AvatarOptimizer.MergePhysBone")));
so.FindProperty("makeParent").boolValue = true;
so.FindProperty("maxAngleXConfig.override").boolValue = true; so.FindProperty("maxAngleXConfig.value").floatValue = 1.3f;   // only for values that differ
so.FindProperty("maxAngleZConfig.override").boolValue = true; so.FindProperty("maxAngleZConfig.value").floatValue = 2f;
var arr = so.FindProperty("componentsSet.mainSet"); arr.arraySize = pbs.Count; for (int i = 0; i < pbs.Count; i++) arr.GetArrayElementAtIndex(i).objectReferenceValue = pbs[i];
so.ApplyModifiedProperties(); UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(av.scene);
return "merged " + pbs.Count + " PhysBones";
```
To find which settings differ, compare `SerializedProperty.DataEquals` across the PhysBones before you choose the overrides.

### B7 — AAO Remove Mesh By BlendShape (hidden body)
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var body = av.transform.Find("Body_Mesh_Path").gameObject;   // list the body's Shrink_* shapes first
var shapes = new[]{ "Shrink_Spine_all", "Shrink_Hip_all", "Shrink_Upper_leg1", "Shrink_Upper_leg2", "Shrink_Knees", "Shrink_Lower_leg" };
var so = new SerializedObject(Undo.AddComponent(body, T("Anatawa12.AvatarOptimizer.RemoveMeshByBlendShape")));
var arr = so.FindProperty("shapeKeysSet.mainSet"); arr.arraySize = shapes.Length; for (int i = 0; i < shapes.Length; i++) arr.GetArrayElementAtIndex(i).stringValue = shapes[i];
so.ApplyModifiedProperties(); UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(av.scene);
return "tolerance=" + so.FindProperty("tolerance").floatValue;
```

### B8 — Meshia Cascading Avatar Mesh Simplifier with manual targets (`rank_target` only)
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var mc = T("Meshia.MeshSimplification.Ndmf.MeshiaCascadingAvatarMeshSimplifier");
var obj = new GameObject("PreuploadMeshia"); Undo.RegisterCreatedObjectUndo(obj, "meshia"); obj.transform.SetParent(av.transform, false);
var c = obj.AddComponent(mc); mc.GetMethod("RefreshEntries").Invoke(c, null);
var targets = new System.Collections.Generic.Dictionary<string,int>{ {"HairMesh", 6500}, {"Shirt", 3200} };   // renderer name -> triangles; respect the per-part caps
var border = new System.Collections.Generic.HashSet<string>{ "HairMesh", "Shirt" };
var so = new SerializedObject(c); so.Update(); so.FindProperty("AutoAdjustEnabled").boolValue = false; so.FindProperty("TargetTriangleCount").intValue = 68000;
var e = so.FindProperty("Entries"); var sb = new System.Text.StringBuilder();
for (int i = 0; i < e.arraySize; i++) { var x = e.GetArrayElementAtIndex(i); var o = x.FindPropertyRelative("RendererObjectReference.targetObject").objectReferenceValue; string n = o != null ? o.name : "?"; int t;
  if (targets.TryGetValue(n, out t)) { x.FindPropertyRelative("Enabled").boolValue = true; x.FindPropertyRelative("TargetTriangleCount").intValue = t;
    x.FindPropertyRelative("Options.PreserveSurfaceCurvature").boolValue = true; x.FindPropertyRelative("Options.PreserveBorderEdges").boolValue = border.Contains(n); sb.AppendLine("simplify " + n + " -> " + t); }
  else { x.FindPropertyRelative("Enabled").boolValue = false; sb.AppendLine("keep " + n + " (" + x.FindPropertyRelative("TargetTriangleCount").intValue + ")"); } }
so.ApplyModifiedProperties(); UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(av.scene);
return sb.ToString();
```
After `RefreshEntries`, each entry's `TargetTriangleCount` equals the renderer's current triangle count, which gives you the budget list. Meshia runs in NDMF's Optimizing phase **before** AAO, so its targets apply to the mesh before AAO removes hidden polygons. The final count can be lower than the target; measure it with B2. Each entry also has `PreserveBorderEdgesBones`, a `ulong` mask of `HumanBodyBones` bits. Its default covers both hands and all fingers, and it only keeps border edges near those bones. It does **not** lock the region, which is why B10 exists.

### B9 — Side-by-side visual check (temporary clone; destroy it afterwards)
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
var clone = UnityEngine.Object.Instantiate(av); clone.name = "PREUPLOAD_VISUAL_CLONE";
nadena.dev.ndmf.AvatarProcessor.ProcessAvatar(clone);
clone.transform.position = av.transform.position + new Vector3(0.8f, 0, 0);
return "head at " + av.GetComponent<Animator>().GetBoneTransform(HumanBodyBones.Head).position;
```
Next, take screenshots with `manage_camera`: `action=screenshot`, `view_position=[0.4,1.05,2.4]`, `view_target=[0.4,0.95,0]`, plus a head close-up at `[0.4,1.57,0.7]`, `include_image=true`, `output_folder=.avatar-preupload/screenshots`. The avatar faces +z, and the processed clone shows on the left. **Because of the NDMF preview, the scene original may already show the reduction.** For a true "before", process a second clone with the suspect component disabled, place it 2 m further away, and shoot the same relative view. Then clean up:
```csharp
foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name.StartsWith("PREUPLOAD_")) UnityEngine.Object.DestroyImmediate(r);
nadena.dev.ndmf.AvatarProcessor.CleanTemporaryAssets(); return "cleaned";
```

### B10 — Split a region (hands) out of a shared skinned mesh so Meshia can treat it separately
Creates two mesh assets (`Assets/_AvatarPreupload/Generated/`). The FBX is untouched; the scene instance gets a mesh override and a new sibling renderer. All BlendShapes, UVs and bone weights are kept. Needs the user's approval.
```csharp
GameObject av = null; foreach (var r in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()) if (r.name == AVATAR) av = r;
string BODY = "Body_Mesh_Name";                                         // renderer that contains the hands
var anim = av.GetComponent<Animator>(); SkinnedMeshRenderer smr = null; foreach (var s0 in av.GetComponentsInChildren<SkinnedMeshRenderer>(true)) if (s0.name == BODY) smr = s0;
if (av.transform.Find(BODY + "_Hands") != null) return "already split";
var src = smr.sharedMesh; var bones = smr.bones; int vc = src.vertexCount;
var handSet = new System.Collections.Generic.HashSet<int>();
for (int hb = 0; hb < 55; hb++) { string n = ((HumanBodyBones)hb).ToString(); if (!(n == "LeftHand" || n == "RightHand" || n.Contains("Thumb") || n.Contains("Index") || n.Contains("Middle") || n.Contains("Ring") || n.Contains("Little"))) continue; var t = anim.GetBoneTransform((HumanBodyBones)hb); if (t != null) { int i = System.Array.IndexOf(bones, t); if (i >= 0) handSet.Add(i); } }
var bw = src.boneWeights; var tris = src.GetTriangles(0); int tc = tris.Length / 3;   // assumes one submesh; check src.subMeshCount first
var handV = new bool[vc]; for (int v = 0; v < vc; v++) handV[v] = handSet.Contains(bw[v].boneIndex0) && bw[v].weight0 >= 0.5f;
var handT = new bool[tc]; for (int t = 0; t < tc; t++) { int c = 0; for (int k = 0; k < 3; k++) if (handV[tris[3*t+k]]) c++; handT[t] = c >= 2; }
var verts = src.vertices; var norms = src.normals; var tans = src.tangents; var cols = src.colors;
System.Func<bool, string, Mesh> Build = (wantHand, nm) => {
  var map = new int[vc]; for (int i = 0; i < vc; i++) map[i] = -1; var order = new System.Collections.Generic.List<int>(); var nt = new System.Collections.Generic.List<int>();
  for (int t = 0; t < tc; t++) { if (handT[t] != wantHand) continue; for (int k = 0; k < 3; k++) { int v = tris[3*t+k]; if (map[v] < 0) { map[v] = order.Count; order.Add(v); } nt.Add(map[v]); } }
  int n2 = order.Count; var m = new Mesh(); m.name = nm; if (n2 > 65535) m.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
  var V = new Vector3[n2]; var N = new Vector3[n2]; var Tg = new Vector4[n2]; var C = new Color[n2]; var B = new BoneWeight[n2];
  for (int i = 0; i < n2; i++) { int o = order[i]; V[i] = verts[o]; N[i] = norms[o]; Tg[i] = tans[o]; if (cols.Length > 0) C[i] = cols[o]; B[i] = bw[o]; }
  m.vertices = V; m.normals = N; m.tangents = Tg; if (cols.Length > 0) m.colors = C;
  for (int ch = 0; ch < 8; ch++) { var attr = (UnityEngine.Rendering.VertexAttribute)((int)UnityEngine.Rendering.VertexAttribute.TexCoord0 + ch); if (!src.HasVertexAttribute(attr)) continue;
    var l = new System.Collections.Generic.List<Vector4>(); src.GetUVs(ch, l); var o2 = new System.Collections.Generic.List<Vector4>(n2); foreach (var i in order) o2.Add(l[i]); m.SetUVs(ch, o2); }
  m.boneWeights = B; m.bindposes = src.bindposes; m.SetTriangles(nt, 0);
  var dv = new Vector3[vc]; var dn = new Vector3[vc]; var dt = new Vector3[vc];
  for (int s1 = 0; s1 < src.blendShapeCount; s1++) for (int f = 0; f < src.GetBlendShapeFrameCount(s1); f++) { src.GetBlendShapeFrameVertices(s1, f, dv, dn, dt); var a = new Vector3[n2]; var b = new Vector3[n2]; var c = new Vector3[n2]; for (int i = 0; i < n2; i++) { a[i] = dv[order[i]]; b[i] = dn[order[i]]; c[i] = dt[order[i]]; } m.AddBlendShapeFrame(src.GetBlendShapeName(s1), src.GetBlendShapeFrameWeight(s1, f), a, b, c); }
  m.bounds = src.bounds; return m; };
var bodyMesh = Build(false, BODY + "_NoHands"); var handMesh = Build(true, BODY + "_Hands");
if (!AssetDatabase.IsValidFolder("Assets/_AvatarPreupload")) AssetDatabase.CreateFolder("Assets", "_AvatarPreupload");
if (!AssetDatabase.IsValidFolder("Assets/_AvatarPreupload/Generated")) AssetDatabase.CreateFolder("Assets/_AvatarPreupload", "Generated");
AssetDatabase.CreateAsset(bodyMesh, AssetDatabase.GenerateUniqueAssetPath("Assets/_AvatarPreupload/Generated/" + BODY + "_NoHands.asset"));
AssetDatabase.CreateAsset(handMesh, AssetDatabase.GenerateUniqueAssetPath("Assets/_AvatarPreupload/Generated/" + BODY + "_Hands.asset")); AssetDatabase.SaveAssets();
Undo.SetCurrentGroupName("Preupload: split hands"); int grp = Undo.GetCurrentGroup();
var w = new float[src.blendShapeCount]; for (int i = 0; i < w.Length; i++) w[i] = smr.GetBlendShapeWeight(i);
var hGO = UnityEngine.Object.Instantiate(smr.gameObject, smr.transform.parent); hGO.name = BODY + "_Hands"; hGO.transform.SetSiblingIndex(smr.transform.GetSiblingIndex() + 1); Undo.RegisterCreatedObjectUndo(hGO, "hands");
foreach (var mb in hGO.GetComponents<MonoBehaviour>()) UnityEngine.Object.DestroyImmediate(mb);   // drop e.g. RemoveMeshByBlendShape copies
var hs = hGO.GetComponent<SkinnedMeshRenderer>(); hs.sharedMesh = handMesh; for (int i = 0; i < w.Length; i++) hs.SetBlendShapeWeight(i, w[i]);
Undo.RecordObject(smr, "body"); smr.sharedMesh = bodyMesh; for (int i = 0; i < w.Length; i++) smr.SetBlendShapeWeight(i, w[i]); PrefabUtility.RecordPrefabInstancePropertyModifications(smr);
Undo.CollapseUndoOperations(grp); UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(av.scene);
return "body " + bodyMesh.triangles.Length / 3 + " tris, hands " + handMesh.triangles.Length / 3 + " tris";
```
Then:
- add the new renderer to Merge Skinned Mesh's `renderersSet.mainSet`;
- call the Meshia component's `RefreshEntries()` (it only appends missing renderers);
- set the hands entry to `Enabled = false` or a capped target with `PreserveSurfaceCurvature` and `PreserveBorderEdges`;
- keep `PreserveBorderEdges` on the body entry.

Before splitting, list the BlendShapes that move hand vertices, and any MA Shape Changer that targets them. Name-matched shapes are merged back by Merge Skinned Mesh, but static Shape Changer weights apply only to the original renderer. **Undo:** delete `<BODY>_Hands`, revert the mesh override on `<BODY>`, and delete its Meshia entry.

### B11 — Pose a processed clone's fingers (fist / point) for validation
```csharp
var c = GameObject.Find("PREUPLOAD_VISUAL_CLONE"); var a = c.GetComponent<Animator>();
var h = new HumanPoseHandler(a.avatar, c.transform); var p = new HumanPose(); h.GetHumanPose(ref p);
bool POINT = true;   // false = fist
for (int m = 0; m < HumanTrait.MuscleCount; m++) { string n = HumanTrait.MuscleName[m]; if (!n.Contains("Stretched")) continue;
  if (n.Contains("Index")) p.muscles[m] = POINT ? 0.8f : -0.7f; else if (n.Contains("Middle") || n.Contains("Ring") || n.Contains("Little") || n.Contains("Thumb")) p.muscles[m] = -0.9f; }
h.SetHumanPose(ref p);
// SetHumanPose also moves the body: put the right index root at a known spot
float X = -2.25f; var hips = a.GetBoneTransform(HumanBodyBones.Hips); var i1 = a.GetBoneTransform(HumanBodyBones.RightIndexProximal);
hips.position += new Vector3(X - i1.position.x, 1.42f - i1.position.y, 0.05f - i1.position.z);
return "index root " + i1.position + ", tip " + a.GetBoneTransform(HumanBodyBones.RightIndexDistal).position;
```
Shoot with `view_position` about `[X+0.1, 1.52, 0.22]` and `view_target` `[X+0.05, 1.41, 0.04]`, then do the same on a clone whose hands entry is disabled.