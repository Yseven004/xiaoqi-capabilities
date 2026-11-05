import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


PUBLISHER = Path(__file__).with_name("publish_package.py")


class PublishPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="xiaoqi-package-")
        self.root = Path(self.temp.name)
        self.package = self.root / "sample-capability"
        self.package.mkdir()
        (self.package / "xiaoqi-capability.json").write_text(
            json.dumps(
                {
                    "id": "sample-capability",
                    "version": "1.0.0",
                    "type": "skill",
                    "display_name": "Sample",
                    "description": "Release fixture",
                    "host_api": 1,
                    "required_tools": [],
                    "runtime": {},
                    "capabilities": [],
                    "mcp": None,
                }
            ),
            encoding="utf-8",
        )
        (self.package / "PROVENANCE.json").write_text("{}", encoding="utf-8")
        (self.package / "LICENSE").write_text("MIT", encoding="utf-8")
        (self.package / "SKILL.md").write_text(
            "---\nname: sample\ndescription: test\n---\nSample instructions.\n",
            encoding="utf-8",
        )
        self.catalog = self.root / "catalog.json"
        self.catalog.write_text(
            json.dumps(
                {"schema_version": 1, "repository": "Yseven004/xiaoqi-capabilities", "packages": []}
            ),
            encoding="utf-8",
        )
        self.commit = "a" * 40

    def tearDown(self):
        self.temp.cleanup()

    def publish(self, output):
        return subprocess.run(
            [
                sys.executable,
                str(PUBLISHER),
                "--root",
                str(self.root),
                "--package",
                "sample-capability",
                "--source-commit",
                self.commit,
                "--output",
                str(output),
                "--catalog-path",
                str(self.catalog),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_archive_is_repeatable_and_catalog_hash_matches(self):
        first = self.root / "first" / "sample-capability.zip"
        second = self.root / "second" / "sample-capability.zip"
        self.assertEqual(self.publish(first).returncode, 0)
        self.assertEqual(self.publish(second).returncode, 0)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        entry = json.loads(self.catalog.read_text(encoding="utf-8"))["packages"][0]
        self.assertEqual(entry["source_commit"], self.commit)
        self.assertEqual(
            entry["asset_url"],
            "https://github.com/Yseven004/xiaoqi-capabilities/releases/download/"
            "sample-capability-v1.0.0/sample-capability.zip",
        )
        with ZipFile(first) as archive:
            self.assertIn("sample-capability/SKILL.md", archive.namelist())

    def test_existing_package_version_cannot_be_replaced(self):
        output = self.root / "sample-capability.zip"
        self.assertEqual(self.publish(output).returncode, 0)
        original = json.loads(self.catalog.read_text(encoding="utf-8"))
        (self.package / "SKILL.md").write_text("different package content", encoding="utf-8")
        result = self.publish(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("immutable", result.stderr)
        self.assertEqual(json.loads(self.catalog.read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main()
