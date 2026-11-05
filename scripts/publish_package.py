#!/usr/bin/env python3
"""Create an immutable package zip and update the public install catalog."""
import argparse
import hashlib
import json
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
    args = parser.parse_args()
    if len(args.source_commit) != 40 or any(c not in "0123456789abcdef" for c in args.source_commit):
        raise SystemExit("source commit must be a full lowercase Git SHA")
    catalog_path = args.root / "catalog.json"
    package_dir = args.root / args.package
    manifest_path = package_dir / "xiaoqi-capability.json"
    if not manifest_path.is_file():
        raise SystemExit("unknown package")
    capability = json.loads(manifest_path.read_text(encoding="utf-8"))
    if capability.get("id") != args.package or capability.get("version") is None:
        raise SystemExit("package identity or version is invalid")
    if not (package_dir / "PROVENANCE.json").is_file() or not any(package_dir.glob("LICENSE*")):
        raise SystemExit("package must retain its provenance and license")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_DEFLATED, compresslevel=9) as bundle:
        for source in sorted(p for p in package_dir.rglob("*") if p.is_file()):
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
        "host_api": capability["host_api"],
        "source_commit": args.source_commit,
        "asset_url": f"https://github.com/Yseven004/xiaoqi-capabilities/releases/download/{args.package}-v{capability['version']}/{args.output.name}",
        "asset_sha256": sha,
        "required_tools": capability.get("required_tools", []),
        "runtime": capability.get("runtime", {}),
        "mcp": capability.get("mcp"),
    }
    rows = [row for row in catalog.get("packages", []) if row.get("id") != args.package]
    rows.append(entry)
    catalog["packages"] = sorted(rows, key=lambda row: row["id"])
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"package": args.package, "version": capability["version"], "sha256": sha}))


if __name__ == "__main__":
    main()
