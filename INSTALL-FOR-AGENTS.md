# Install guide for AI agents

You are an AI agent asked to install the **avatar-preupload-optimization-check** skill from
`https://github.com/Megapotatosan/avatar-preupload-optimization-check`. Follow these steps in order. Tell the user what you did at the end.

The skill is the folder `skills/avatar-preupload-optimization-check/`, which contains `SKILL.md` and `scripts/precheck.py`. The folder name must stay `avatar-preupload-optimization-check`.

## 1. Identify where you are running

Pick the **first** row that matches you:

| You are | Install method | Go to |
|---|---|---|
| Claude Code (terminal, IDE extension, or desktop local session) | Plugin marketplace | [2A](#2a-claude-code) |
| OpenAI Codex (CLI, IDE extension, or app) | Copy the folder to `~/.agents/skills/` | [2B](#2b-openai-codex) |
| Claude app chat (claude.ai / desktop / Cowork) without a shell on the user's machine | The user uploads a ZIP | [2C](#2c-claude-app-upload-by-the-user) |
| Any other agent with a skills folder (Cursor, Gemini CLI, Windsurf, …) | Copy the folder | [2D](#2d-other-agents) |
| No skill system at all | Read `SKILL.md` as instructions | [2E](#2e-no-skill-system) |

Before changing anything, check whether a copy already exists, for example `~/.claude/skills/avatar-preupload-optimization-check/` or `~/.agents/skills/avatar-preupload-optimization-check/`. If it exists and differs, **ask the user** before overwriting it, and back it up to `<folder>.bak-<date>`.

## 2A. Claude Code

Run in the user's shell. In a session, use the same commands with a `/` prefix (`/plugin …`).

```bash
claude plugin marketplace add Megapotatosan/avatar-preupload-optimization-check
claude plugin install avatar-preupload-optimization-check@megapotatosan-vrchat
```

**Verify:** `claude plugin details avatar-preupload-optimization-check` lists `Skills (1) avatar-preupload-optimization-check`. In a running session, run `/reload-plugins`.

**Fallback,** if plugins are blocked by policy: install it as a personal skill instead.

```bash
git clone --depth 1 https://github.com/Megapotatosan/avatar-preupload-optimization-check /tmp/apoc
mkdir -p ~/.claude/skills
cp -r /tmp/apoc/skills/avatar-preupload-optimization-check ~/.claude/skills/
```

On Windows PowerShell:

```powershell
git clone --depth 1 https://github.com/Megapotatosan/avatar-preupload-optimization-check $env:TEMP\apoc
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force "$env:TEMP\apoc\skills\avatar-preupload-optimization-check" "$HOME\.claude\skills\"
```

Claude Code watches skill folders, so no restart is needed.

## 2B. OpenAI Codex

Codex reads user skills from `$HOME/.agents/skills` and repository skills from `<repo>/.agents/skills`. Ask the user which one they want; the default is the user level.

```bash
git clone --depth 1 https://github.com/Megapotatosan/avatar-preupload-optimization-check /tmp/apoc
mkdir -p ~/.agents/skills
cp -r /tmp/apoc/skills/avatar-preupload-optimization-check ~/.agents/skills/
```

On Windows PowerShell:

```powershell
git clone --depth 1 https://github.com/Megapotatosan/avatar-preupload-optimization-check $env:TEMP\apoc
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force "$env:TEMP\apoc\skills\avatar-preupload-optimization-check" "$HOME\.agents\skills\"
```

**Verify:** `~/.agents/skills/avatar-preupload-optimization-check/SKILL.md` exists. If the skill doesn't appear, tell the user to restart Codex.

## 2C. Claude app (upload by the user)

You can't install this yourself. Give the user these steps:

1. Download `avatar-preupload-optimization-check.zip` from
   `https://github.com/Megapotatosan/avatar-preupload-optimization-check/releases/latest`.
2. In Claude, turn on **Settings → Capabilities → Code execution and file creation**.
3. In the same page's **Skills** section, click **Upload skill** and choose the ZIP. Don't unzip it first.

This needs a Pro, Max, Team or Enterprise plan. If you can run code, you may build the ZIP yourself with `python tools/build_zip.py` and hand it to the user.

## 2D. Other agents

Copy `skills/avatar-preupload-optimization-check/` into the agent's documented skills directory, keeping the folder name. Use the clone commands above. If you don't know the directory, ask the user rather than guessing.

## 2E. No skill system

Save the folder somewhere stable, for example `~/avatar-preupload-optimization-check/`. Tell the user to start future requests with:
"Read `<path>/SKILL.md` and follow it."

## 3. Optional: check prerequisites for the user's project

Only if the user gives you their Unity project path and you have a shell on that machine, run the read-only pre-check:

```bash
python ~/.claude/skills/avatar-preupload-optimization-check/scripts/precheck.py "<UnityProject>" --target pc
```

Adjust the path to wherever you installed the skill. On Windows, `py` may replace `python`. Exit code 0 means PASS, 1 means WARN only, and 2 means FAIL. Summarise the result. **Don't install Unity packages yourself**: tell the user what to add in VCC/ALCOM.

The skill works best with the **MCP for Unity** bridge. The setup steps are in `SKILL.md` under "Unity bridge setup". Offer them; don't run them unasked.

## 4. Report to the user

Tell the user:
- where the skill was installed and which method you used;
- how to use it, for example: "Check my avatar before upload. The project is at `<path>`";
- that it is **quality-first** by default and never uploads.

## Update / uninstall

| Method | Update | Uninstall |
|---|---|---|
| Claude Code plugin | `claude plugin marketplace update megapotatosan-vrchat` | `claude plugin uninstall avatar-preupload-optimization-check@megapotatosan-vrchat` |
| Copied folder | Re-clone, then replace the folder (back up the old one first) | Delete the folder, after confirming with the user |
| Claude app | Upload the new ZIP | Settings → Capabilities → Skills → remove |
