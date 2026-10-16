"""Tests for skills/avatar-preupload-optimization-check/scripts/precheck.py (stdlib only).

Run: python -m unittest discover -s tests -v
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "skills", "avatar-preupload-optimization-check")
SCRIPT = os.path.join(SKILL_DIR, "scripts", "precheck.py")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
MAKE_MOCK = os.path.join(ROOT, "tests", "make_mock.py")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_precheck():
    spec = importlib.util.spec_from_file_location("precheck", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_on_mock(variant, target="pc"):
    tmp = tempfile.mkdtemp(prefix=f"mock_{variant}_")
    subprocess.run([sys.executable, MAKE_MOCK, tmp, variant], check=True)
    p = subprocess.run([sys.executable, SCRIPT, tmp, "--target", target, "--json"],
                       capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)


class EmbeddedCopy(unittest.TestCase):
    def test_skill_md_embeds_identical_script(self):
        s = read(SKILL_MD)
        a = s.index("```python\n") + len("```python\n")
        b = s.index("\n```\n", a) + 1
        self.assertEqual(s[a:b], read(SCRIPT),
                         "Appendix A in SKILL.md differs from scripts/precheck.py")

    def test_frontmatter(self):
        s = read(SKILL_MD)
        self.assertTrue(s.startswith("---\n"))
        fm = s.split("---", 2)[1]
        self.assertIn("name:", fm)
        self.assertIn("description:", fm)
        self.assertIn("avatar-preupload-optimization-check", fm)
        self.assertEqual(s.count("```") % 2, 0, "unbalanced code fences")


class Semver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_precheck()

    def test_ranges(self):
        sat = self.m.satisfies
        cases = [
            ("1.10.0", ">=1.10.0", True), ("1.9.4", ">=1.10.0", False),
            ("1.2.3", "^1.2.1", True), ("2.0.0", "^1.2.1", False),
            ("0.5.0", "^0.5.0", True), ("0.6.0", "^0.5.0", False),
            ("1.2.9", "~1.2.0", True), ("1.3.0", "~1.2.0", False),
            ("3.5.2", "3.5.x", True), ("3.6.0", "3.5.x", False),
            ("3.10.5", ">=3.7.0 <3.11.0", True), ("3.11.0", ">=3.7.0 <3.11.0", False),
            ("3.10.1", "3.7.0 - 3.10", True), ("3.11.0", "3.7.0 - 3.10", False),
            ("1.0.0", "<1.0.0 || >=2.0.0", False), ("2.1.0", "<1.0.0 || >=2.0.0", True),
            ("1.0.0-beta.1", ">=1.0.0", False), ("1.0.0", "", True),
        ]
        for ver, rng, want in cases:
            with self.subTest(ver=ver, rng=rng):
                self.assertIs(sat(ver, rng), want)


class MockProjects(unittest.TestCase):
    def test_good_project_passes(self):
        code, out = run_on_mock("good")
        self.assertEqual(code, 0, json.dumps(out["checks"], indent=1))
        files = {a["file"].replace("\\", "/"): a for a in out["avatars"]}
        self.assertIn("Assets/Avatars/MyAvatar.prefab", files)
        self.assertIn("Assets/Avatars/MyAvatar_Variant2.prefab", files)   # variant of a variant
        self.assertEqual(files["Assets/Scenes/Main.unity"]["avatar_prefab_instances"], 2)

    def test_bad_project_fails(self):
        code, out = run_on_mock("bad", target="both")
        self.assertEqual(code, 2)
        fails = {c["check"] for c in out["checks"] if c["status"] == "FAIL"}
        for expected in ("Packages resolved", "Dependency", "Legacy duplicate", "Package: VRCQuestTools"):
            self.assertIn(expected, fails)

    def test_not_vcc(self):
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "Assets"))
        p = subprocess.run([sys.executable, SCRIPT, tmp], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
