"""Package the skill folder as a ZIP for upload to Claude (Settings > Capabilities > Skills).

Usage: python tools/build_zip.py [out_dir]   ->  <out_dir>/avatar-preupload-optimization-check.zip
The ZIP contains the folder `avatar-preupload-optimization-check/` with SKILL.md and scripts/.
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "avatar-preupload-optimization-check"
SRC = os.path.join(ROOT, "skills", NAME)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, NAME + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(SRC):
            dns[:] = [d for d in dns if d != "__pycache__"]
            for fn in sorted(fns):
                full = os.path.join(dp, fn)
                z.write(full, os.path.join(NAME, os.path.relpath(full, SRC)).replace(os.sep, "/"))
    print(out)


if __name__ == "__main__":
    main()
