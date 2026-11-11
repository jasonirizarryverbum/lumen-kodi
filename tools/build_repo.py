"""Package every addon under src/ into the Kodi repository served from docs/.

Usage:  python -I tools/build_repo.py

Output (GitHub Pages serves docs/):
  docs/index.html                      page Kodi's file manager can browse
  docs/repository.lumen-<ver>.zip      the one zip you install by hand
  docs/repo/addons.xml(.md5)           repository index
  docs/repo/zips/<id>/<id>-<ver>.zip   addon packages
"""
import hashlib
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lumen_art import write_icon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
DOCS = ROOT / "docs"
ZIPS = DOCS / "repo" / "zips"
SKIP = {".git", "__pycache__", ".DS_Store", "Thumbs.db"}


def package(addon_dir):
    tree = ET.parse(addon_dir / "addon.xml")
    root = tree.getroot()
    addon_id, version = root.get("id"), root.get("version")
    if addon_id != addon_dir.name:
        raise SystemExit(f"{addon_dir.name}: folder name must match addon id {addon_id}")

    icon_rel = root.findtext(".//assets/icon") or "icon.png"
    write_icon(addon_dir / icon_rel)

    out = ZIPS / addon_id
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{addon_id}-{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(addon_dir.rglob("*")):
            if path.is_file() and not (set(path.parts) & SKIP) and path.suffix != ".pyc":
                zf.write(path, f"{addon_id}/{path.relative_to(addon_dir).as_posix()}")
    (out / icon_rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(addon_dir / icon_rel, out / icon_rel)
    print(f"  {target.relative_to(ROOT)}  ({target.stat().st_size // 1024} KB)")
    return root, target


def main():
    if ZIPS.exists():
        shutil.rmtree(ZIPS)
    for old in DOCS.glob("repository.lumen-*.zip"):
        old.unlink()
    DOCS.mkdir(exist_ok=True)

    index = ET.Element("addons")
    repo_zip = None
    for addon_dir in sorted(p for p in SRC.iterdir() if (p / "addon.xml").is_file()):
        root, target = package(addon_dir)
        index.append(root)
        if root.get("id") == "repository.lumen":
            repo_zip = target

    body = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(index, encoding="utf-8") + b"\n"
    (DOCS / "repo" / "addons.xml").write_bytes(body)
    (DOCS / "repo" / "addons.xml.md5").write_text(hashlib.md5(body).hexdigest(), encoding="ascii")

    shutil.copyfile(repo_zip, DOCS / repo_zip.name)
    (DOCS / ".nojekyll").write_text("", encoding="ascii")
    (DOCS / "index.html").write_text(
        "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>Lumen for Kodi</title></head>\n"
        "<body>\n<h1>Lumen for Kodi</h1>\n"
        "<p>Add this page's address as a source in Kodi's file manager, then use "
        "Add-ons &gt; Install from zip file and pick the file below.</p>\n"
        f"<a href=\"{repo_zip.name}\">{repo_zip.name}</a>\n</body></html>\n",
        encoding="utf-8",
    )
    print("repository index written to docs/repo/addons.xml")


if __name__ == "__main__":
    main()
