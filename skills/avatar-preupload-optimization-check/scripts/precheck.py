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
    # Windows consoles / captured pipes often default to cp1252 or cp950, which can't encode the
    # status icons and arrows below; force UTF-8 so the script never crashes on output.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
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
