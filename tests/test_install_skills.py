import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SMALL = "web-design-guidelines"


class InstallSkillsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-test-")
        self.addCleanup(self.temp.cleanup)
        self.dest = Path(self.temp.name) / "project with spaces" / ".agents" / "skills"

    def run_install(self, *args, root=ROOT):
        return subprocess.run(
            [sys.executable, str(root / "install_skills.py"), "--dest", str(self.dest), *args],
            cwd=self.temp.name, capture_output=True, text=True,
        )

    def test_all_skills_install_with_complete_contents_and_repeat_cleanly(self):
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((ROOT / "skills-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(list(self.dest.iterdir())), 8)
        for name, package in manifest["skills"].items():
            for relative in package["files"]:
                self.assertEqual((ROOT / "skills" / name / relative).read_bytes(),
                                 (self.dest / name / relative).read_bytes())
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("Already installed:"), 8)

    def test_selected_skill_only(self):
        result = self.run_install("--skills", SMALL)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([p.name for p in self.dest.iterdir()], [SMALL])

    def test_conflict_does_not_partially_install_or_overwrite(self):
        target = self.dest / SMALL
        target.mkdir(parents=True)
        (target / "custom.txt").write_text("local version")
        result = self.run_install()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([p.name for p in self.dest.iterdir()], [SMALL])
        self.assertEqual((target / "custom.txt").read_text(), "local version")

    def test_force_preserves_previous_version_outside_discovery_directory(self):
        target = self.dest / SMALL
        target.mkdir(parents=True)
        (target / "custom.txt").write_text("keep this version")
        result = self.run_install("--skills", SMALL, "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((target / "SKILL.md").is_file())
        backups = list((self.dest.parent / ".skill-backups").glob("*/" + SMALL + "/custom.txt"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "keep this version")

    def test_unknown_name_fails_without_creating_destination(self):
        result = self.run_install("--skills", "missing-skill")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.dest.exists())

    def test_damaged_package_fails_before_installation(self):
        source = Path(self.temp.name) / "damaged source"
        source.mkdir()
        for name in ("install_skills.py", "skills-manifest.json"):
            shutil.copy2(str(ROOT / name), str(source / name))
        shutil.copytree(str(ROOT / "skills" / SMALL), str(source / "skills" / SMALL))
        (source / "skills" / SMALL / "SKILL.md").write_text("damaged")
        result = self.run_install("--skills", SMALL, root=source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("integrity check failed", result.stderr)
        self.assertFalse(self.dest.exists())

    def test_check_is_read_only(self):
        result = self.run_install("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.dest.exists())


if __name__ == "__main__":
    unittest.main()
