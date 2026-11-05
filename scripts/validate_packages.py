#!/usr/bin/env python3
"""Fast checks for independent package boundaries and release metadata."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("study-notes-studio", "book-to-skill", "original-reading-annotations", "learning-notes-manager")


def main() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    assert catalog == {"schema_version": 1, "repository": "Yseven004/xiaoqi-capabilities", "packages": []} or catalog["schema_version"] == 1
    for package in PACKAGES:
        path = ROOT / package
        metadata = json.loads((path / "xiaoqi-capability.json").read_text(encoding="utf-8"))
        provenance = json.loads((path / "PROVENANCE.json").read_text(encoding="utf-8"))
        assert metadata["id"] == package and metadata["host_api"] == 1
        assert re.fullmatch(r"\d+\.\d+\.\d+", metadata["version"])
        assert provenance.get("license") and any(path.glob("LICENSE*"))
        assert not any(p.suffix in {".sqlite3", ".env", ".pem", ".key"} for p in path.rglob("*"))
        if metadata["type"] == "skill":
            assert (path / "SKILL.md").is_file()
        else:
            assert (path / "plugin.json").is_file()
            plugin = json.loads((path / "plugin.json").read_text(encoding="utf-8"))
            assert plugin["name"] == package
    annotation = ROOT / "original-reading-annotations"
    script = (annotation / "skills/annotate/scripts/annotate.py").read_text(encoding="utf-8")
    assert "assets" in script and "LongCang-Regular.ttf" in script
    assert (annotation / "assets/fonts/OFL.txt").is_file()
    notes = (ROOT / "learning-notes-manager/skills/notes/SKILL.md").read_text(encoding="utf-8")
    assert "append_learning_notes" in notes
    print("CAPABILITY_PACKAGES_OK " + ",".join(PACKAGES))


if __name__ == "__main__":
    main()
