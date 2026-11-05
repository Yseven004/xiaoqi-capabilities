import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class XiaoqiExtractionTests(unittest.TestCase):
    def test_entrypoint_persists_chinese_extraction_outputs(self):
        source = PACKAGE_ROOT / "tests" / "fixtures" / "learning-source.md"
        with tempfile.TemporaryDirectory(prefix="book-extraction-test-") as temp:
            output = Path(temp) / "output"
            environment = os.environ.copy()
            environment["XIAOQI_BOOK_OUTPUT_DIR"] = str(output)
            result = subprocess.run(
                [
                    sys.executable,
                    str(PACKAGE_ROOT / "scripts" / "xiaoqi_extract.py"),
                    str(source),
                ],
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (output / "book-extraction" / "full_text.txt").read_text(
                encoding="utf-8"
            )
            self.assertIn("第一章", text)
            self.assertIn("反模式", text)
            self.assertIn("第二章", text)
            self.assertIn("先回忆，再核对", text)
            self.assertTrue(
                (output / "book-extraction" / "metadata.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
