"""Build a fake VCC/ALCOM Unity project for precheck tests.

Usage: python make_mock.py <out_dir> good|bad
"""
import json, os, sys, uuid
root, variant = sys.argv[1], sys.argv[2]
def w(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(s)
def pkg(name, ver, deps=None, legacy=None, scripts=()):
    d = os.path.join(root, "Packages", name)
    j = {"name": name, "version": ver, "vpmDependencies": deps or {}}
    if legacy: j["legacyFolders"] = legacy
    w(os.path.join(d, "package.json"), json.dumps(j))
    g = {}
    for s in scripts:
        gid = uuid.uuid4().hex
        w(os.path.join(d, "Runtime", s + ".cs"), "// stub")
        w(os.path.join(d, "Runtime", s + ".cs.meta"), f"fileFormatVersion: 2\nguid: {gid}\n")
        g[s] = gid
    return g
w(f"{root}/ProjectSettings/ProjectVersion.txt", "m_EditorVersion: 2022.3.22f1\n")
os.makedirs(f"{root}/Library/PackageCache", exist_ok=True)
pk = {"com.vrchat.base": "3.10.1", "com.vrchat.avatars": "3.10.1", "nadena.dev.ndmf": "1.11.0",
      "com.anatawa12.avatar-optimizer": "1.9.19", "dev.limitex.avatar-compressor": "0.5.0",
      "jp.lilxyzw.avatar-utils": "2.1.2", "com.ramtype0.meshia.mesh-simplification": "3.2.0",
      "com.github.kurotu.vrc-quest-tools": "2.11.7", "com.anatawa12.custom-localization-for-editor-extension": "1.2.2"}
if variant == "bad":
    pk["nadena.dev.ndmf"] = "1.9.4"           # too old for LAC
    del pk["com.ramtype0.meshia.mesh-simplification"]
    del pk["com.github.kurotu.vrc-quest-tools"]
manifest = {"dependencies": {k: {"version": v} for k, v in pk.items()}, "locked": {k: {"version": v} for k, v in pk.items()}}
if variant == "bad":
    manifest["locked"]["jp.lilxyzw.liltoon"] = {"version": "1.8.5"}   # in manifest, folder missing
w(f"{root}/Packages/vpm-manifest.json", json.dumps(manifest))
guids = {}
for name, ver in pk.items():
    deps = {}
    legacy = None
    scripts = ()
    if name == "com.anatawa12.avatar-optimizer":
        deps = {"nadena.dev.ndmf": ">=1.8.0 <2.0.0", "com.vrchat.avatars": ">=3.7.0 <3.11.0"}
        legacy = {"Assets\\AvatarOptimizer": "abc"}; scripts = ("TraceAndOptimize", "MergeSkinnedMesh")
    if name == "dev.limitex.avatar-compressor":
        deps = {"com.vrchat.base": ">=3.10.0", "com.vrchat.avatars": ">=3.10.0", "nadena.dev.ndmf": ">=1.10.0"}
        scripts = ("TextureCompressor",)
    if name == "com.ramtype0.meshia.mesh-simplification":
        deps = {"com.anatawa12.custom-localization-for-editor-extension": "^1.2.1"}
    guids.update(pkg(name, ver, deps, legacy, scripts))
sdk = uuid.uuid4().hex
w(f"{root}/Packages/com.vrchat.avatars/Runtime/VRC.SDK3A.dll.meta", f"guid: {sdk}\n")
desc = f"--- !u!114 &1\nMonoBehaviour:\n  m_Script: {{fileID: 542108242, guid: {sdk}, type: 3}}\n  customizeAnimationLayers: 1\n"
to = f"--- !u!114 &2\nMonoBehaviour:\n  m_Script: {{fileID: 11500000, guid: {guids['TraceAndOptimize']}, type: 3}}\n"
lac = f"--- !u!114 &3\nMonoBehaviour:\n  m_Script: {{fileID: 11500000, guid: {guids['TextureCompressor']}, type: 3}}\n"
miss = f"--- !u!114 &4\nMonoBehaviour:\n  m_Script: {{fileID: 11500000, guid: {'9'*32}, type: 3}}\n"
body = "%YAML 1.1\n" + desc + to + (lac if variant == "good" else miss)
w(f"{root}/Assets/Avatars/MyAvatar.prefab", body)
w(f"{root}/Assets/Scenes/Empty.unity", "%YAML 1.1\n--- !u!1 &1\nGameObject:\n")
if variant == "good":
    os.makedirs(f"{root}/.git", exist_ok=True)
else:
    os.makedirs(f"{root}/Assets/AvatarOptimizer", exist_ok=True)   # legacy dup
    os.makedirs(f"{root}/Assets/MantisLODEditor", exist_ok=True)   # mantis core, no ndmf wrapper
if variant == "good":
    # prefab variant chain + scene instances (no descriptor serialized in these files)
    w(f"{root}/Assets/Avatars/MyAvatar.prefab.meta", "fileFormatVersion: 2\nguid: " + "a" * 31 + "1\n")
    w(f"{root}/Assets/Avatars/MyAvatar_Variant.prefab.meta", "fileFormatVersion: 2\nguid: " + "a" * 31 + "2\n")
    w(f"{root}/Assets/Avatars/MyAvatar_Variant2.prefab.meta", "fileFormatVersion: 2\nguid: " + "a" * 31 + "3\n")
    inst = "--- !u!1001 &{n}\nPrefabInstance:\n  m_SourcePrefab: {{fileID: 100100000, guid: {g}, type: 3}}\n"
    w(f"{root}/Assets/Avatars/MyAvatar_Variant.prefab", "%YAML 1.1\n" + inst.format(n=1, g="a" * 31 + "1"))
    w(f"{root}/Assets/Avatars/MyAvatar_Variant2.prefab", "%YAML 1.1\n" + inst.format(n=1, g="a" * 31 + "2"))
    w(f"{root}/Assets/Scenes/Main.unity", "%YAML 1.1\n" + inst.format(n=1, g="a" * 31 + "3")
      + inst.format(n=2, g="a" * 31 + "2") + inst.format(n=3, g="b" * 32))
