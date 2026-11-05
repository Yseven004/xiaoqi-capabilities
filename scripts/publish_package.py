#!/usr/bin/env python3
"""Create an immutable package zip and update the public install catalog."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--catalog-path", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", args.package):
        raise SystemExit("package id is invalid")
    if len(args.source_commit) != 40 or any(c not in "0123456789abcdef" for c in args.source_commit):
        raise SystemExit("source commit must be a full lowercase Git SHA")
    catalog_path = args.catalog_path or args.root / "catalog.json"
    package_dir = args.root / args.package
    manifest_path = package_dir / "xiaoqi-capability.json"
    if package_dir.is_symlink() or not package_dir.is_dir() or not manifest_path.is_file():
        raise SystemExit("unknown package")
    capability = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = capability.get("version", "")
    if (capability.get("id") != args.package or
            not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version) or
            capability.get("host_api") != 1 or
            not isinstance(capability.get("display_name"), str) or
            not isinstance(capability.get("description"), str)):
        raise SystemExit("package identity or version is invalid")
    if not (package_dir / "PROVENANCE.json").is_file() or not any(package_dir.glob("LICENSE*")):
        raise SystemExit("package must retain its provenance and license")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED, compresslevel=9) as bundle:
        sources = []
        for source in package_dir.rglob("*"):
            relative_parts = source.relative_to(package_dir).parts
            if any(part in {"__pycache__", ".pytest_cache", ".venv"} for part in relative_parts):
                continue
            if source.suffix in {".pyc", ".pyo"}:
                continue
            if source.is_symlink():
                raise SystemExit(f"symbolic links are not allowed: {source}")
            if source.is_file():
                sources.append(source)
        for source in sorted(sources):
            relative = source.relative_to(package_dir).as_posix()
            info = ZipInfo(f"{args.package}/{relative}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, source.read_bytes())
    sha = digest(args.output)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1 or catalog.get("repository") != "Yseven004/xiaoqi-capabilities":
        raise SystemExit("catalog identity is invalid")
    entry = {
        "id": args.package,
        "version": capability["version"],
        "type": capability["type"],
        "display_name": capability["display_name"],
        "description": capability["description"],
        "host_api": capability["host_api"],
        "source_commit": args.source_commit,
        "asset_url": f"https://github.com/Yseven004/xiaoqi-capabilities/releases/download/{args.package}-v{capability['version']}/{args.output.name}",
        "asset_sha256": sha,
        "required_tools": capability.get("required_tools", []),
        "runtime": capability.get("runtime", {}),
        "capabilities": capability.get("capabilities", []),
        "mcp": capability.get("mcp"),
    }
    rows = [row for row in catalog.get("packages", []) if row.get("id") != args.package]
    previous = next((row for row in catalog.get("packages", []) if row.get("id") == args.package), None)
    if previous is not None:
        if previous["version"] == entry["version"]:
            if any(previous.get(key) != value for key, value in entry.items()):
                raise SystemExit("published package versions are immutable")
        elif tuple(map(int, entry["version"].split("."))) <= tuple(map(int, previous["version"].split("."))):
            raise SystemExit("new package version must increase")
    rows.append(entry)
    catalog["packages"] = sorted(rows, key=lambda row: row["id"])
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"package": args.package, "version": capability["version"], "sha256": sha}))


if __name__ == "__main__":
    main()
