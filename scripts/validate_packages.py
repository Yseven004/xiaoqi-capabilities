#!/usr/bin/env python3
"""Fast checks for independent package boundaries and release metadata."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INITIAL_PACKAGES = {
    "study-notes-studio",
    "book-to-skill",
    "original-reading-annotations",
    "learning-notes-manager",
}
PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
VERSION = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
HOST_TOOLS = {
    "read_skill_resource",
    "execute_skill_script",
    "set_task_deliverables",
    "generate_image",
    "append_learning_notes",
}
CAPABILITIES = {"image.annotate_original", "learning_notes.append"}


def main() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["repository"] == "Yseven004/xiaoqi-capabilities"
    package_dirs = sorted(
        path for path in ROOT.iterdir()
        if path.is_dir() and (path / "xiaoqi-capability.json").is_file()
    )
    packages = {path.name: path for path in package_dirs}
    assert INITIAL_PACKAGES <= packages.keys()
    rows = catalog.get("packages", [])
    assert isinstance(rows, list) and len(rows) <= 100
    assert len({row.get("id") for row in rows}) == len(rows)
    for row in rows:
        assert row["id"] in packages and PACKAGE_ID.fullmatch(row["id"])
        assert re.fullmatch(r"[0-9a-f]{40}", row["source_commit"])
        assert re.fullmatch(r"[0-9a-f]{64}", row["asset_sha256"])
        assert VERSION.fullmatch(row["version"])
        manifest = json.loads((packages[row["id"]] / "xiaoqi-capability.json").read_text(encoding="utf-8"))
        assert tuple(map(int, row["version"].split("."))) <= tuple(
            map(int, manifest["version"].split("."))
        )
        assert row["asset_url"] == (
            f"https://github.com/Yseven004/xiaoqi-capabilities/releases/download/"
            f"{row['id']}-v{row['version']}/{row['id']}.zip"
        )
    for package, path in packages.items():
        metadata = json.loads((path / "xiaoqi-capability.json").read_text(encoding="utf-8"))
        provenance = json.loads((path / "PROVENANCE.json").read_text(encoding="utf-8"))
        assert metadata["id"] == package and metadata["host_api"] == 1
        assert PACKAGE_ID.fullmatch(package)
        assert VERSION.fullmatch(metadata["version"])
        assert metadata["type"] in {"skill", "plugin"}
        assert metadata.get("display_name") and metadata.get("description")
        assert isinstance(metadata.get("required_tools"), list)
        assert all(isinstance(tool, str) for tool in metadata["required_tools"])
        assert set(metadata["required_tools"]) <= HOST_TOOLS
        assert isinstance(metadata.get("runtime", {}), dict)
        assert metadata.get("mcp") is None or isinstance(metadata["mcp"], dict)
        assert all(isinstance(capability, str) for capability in metadata.get("capabilities", []))
        assert set(metadata.get("capabilities", [])) <= CAPABILITIES
        assert provenance.get("license") and any(path.glob("LICENSE*"))
        assert not any(p.suffix.lower() in {".sqlite3", ".env", ".pem", ".key"} for p in path.rglob("*"))
        if metadata["type"] == "skill":
            assert (path / "SKILL.md").is_file()
        else:
            assert (path / "plugin.json").is_file()
            plugin = json.loads((path / "plugin.json").read_text(encoding="utf-8"))
            assert plugin["name"] == package
    annotation = packages["original-reading-annotations"]
    script = (annotation / "skills/annotate/scripts/annotate.py").read_text(encoding="utf-8")
    assert "assets" in script and "LongCang-Regular.ttf" in script
    assert (annotation / "assets/fonts/OFL.txt").is_file()
    notes = (ROOT / "learning-notes-manager/skills/notes/SKILL.md").read_text(encoding="utf-8")
    assert "append_learning_notes" in notes
    assert "learning_notes.append" in json.loads(
        (packages["learning-notes-manager"] / "xiaoqi-capability.json").read_text(encoding="utf-8")
    )["capabilities"]
    assert "image.annotate_original" in json.loads(
        (annotation / "xiaoqi-capability.json").read_text(encoding="utf-8")
    )["capabilities"]
    print("CAPABILITY_PACKAGES_OK " + ",".join(packages))


if __name__ == "__main__":
    main()
