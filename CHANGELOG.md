# Changelog

## 1.0.0 — 2026-10-16

First public release.

- Quality-first by default: lossless optimizations only, and PC Very Poor is accepted. Use `rank_target` mode to reduce polygons toward a named rank.
- Phase 0 project pre-check (`precheck.py`, stdlib only):
  - checks that VCC/ALCOM packages are present, resolved and dependency-compatible;
  - finds legacy `.unitypackage` duplicates;
  - discovers avatars, including prefab variants and scene instances.
- Per-part polygon-reduction caps, learned from in-game failures (hands, tight clothing, hair cards).
- Tested Unity bridge recipes for MCP for Unity `execute_code`, B1–B11:
  - audit
  - toggle map
  - EditorOnly removal with a reference scan
  - Merge Skinned Mesh
  - Merge PhysBone
  - Remove Mesh By BlendShape
  - Meshia
  - visual compare
  - hand-mesh split
  - finger pose test
- Works with any agent: Claude Code, Claude (claude.ai / desktop / Cowork), OpenAI Codex, and other agents that read `SKILL.md`.
