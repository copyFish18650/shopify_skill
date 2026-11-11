#!/usr/bin/env python3
"""Install complete skill folders using only the Python standard library."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def file_hashes(directory):
    return {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.suffix not in (".pyc", ".pyo")
        and p.name != ".DS_Store"
    }


def verify_source(name, expected):
    actual = file_hashes(SKILLS / name)
    if actual != expected:
        changed = sorted(set(actual) | set(expected))
        changed = [p for p in changed if actual.get(p) != expected.get(p)]
        raise ValueError("Package integrity check failed for {}: {}".format(
            name, ", ".join(changed[:8])))


def within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def install_one(name, dest, expected, force):
    target = dest / name
    if target.exists() and target.is_dir() and file_hashes(target) == expected:
        print("Already installed: " + name)
        return
    if target.is_symlink():
        raise ValueError("Refusing to replace a symlink: " + str(target))
    if target.exists() and not force:
        raise ValueError("Skill already exists: {}. Use --force to back it up and replace it.".format(target))

    backup = None
    with tempfile.TemporaryDirectory(prefix=".skill-install-", dir=str(dest.parent)) as tmp:
        staged = Path(tmp) / name
        shutil.copytree(str(SKILLS / name), str(staged), ignore=IGNORE)
        if file_hashes(staged) != expected:
            raise ValueError("Copied skill failed verification: " + name)
        if target.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = dest.parent / ".skill-backups" / stamp / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            target.rename(backup)
        try:
            staged.rename(target)
        except OSError:
            if backup is not None:
                backup.rename(target)
            raise
    print("Installed: {} -> {}".format(name, target))
    if backup is not None:
        print("Previous version backed up: " + str(backup))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List available skills without installing")
    parser.add_argument("--check", action="store_true", help="Check package hashes without installing")
    parser.add_argument("--skills", nargs="+", metavar="NAME", help="Install selected skills; defaults to all eight")
    parser.add_argument("--dest", type=Path, default=Path.home() / ".agents" / "skills",
                        help="Skills directory; defaults to ~/.agents/skills")
    parser.add_argument("--force", action="store_true", help="Back up and replace existing skills")
    args = parser.parse_args()
    try:
        manifest = json.loads((ROOT / "skills-manifest.json").read_text(encoding="utf-8"))
        if manifest.get("schema_version") != 1:
            raise ValueError("Unsupported skill manifest version")
        packages = manifest["skills"]
        names = list(dict.fromkeys(args.skills or sorted(packages)))
        unknown = set(names) - set(packages)
        if unknown:
            raise ValueError("Unknown skills: " + ", ".join(sorted(unknown)))
        if args.list:
            print("\n".join(names))
            return 0
        for name in names:
            verify_source(name, packages[name]["files"])
        if args.check:
            print("Verified {} complete skill packages.".format(len(names)))
            return 0
        dest = args.dest.expanduser().resolve()
        if within(dest, SKILLS) or within(SKILLS, dest):
            raise ValueError("Installation destination must not overlap the source skills directory")
        # Check conflicts for the whole selection before changing any installed skill.
        for name in names:
            target = dest / name
            if target.is_symlink():
                raise ValueError("Refusing to replace a symlink: " + str(target))
            if target.exists() and not args.force:
                if not target.is_dir() or file_hashes(target) != packages[name]["files"]:
                    raise ValueError("Skill already exists: {}. Use --force to back it up and replace it.".format(target))
        dest.mkdir(parents=True, exist_ok=True)
        for name in names:
            install_one(name, dest, packages[name]["files"], args.force)
        print("Done. Start a new agent session; restart the app if the skills do not appear.")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, "Error: {}\n".format(exc))


if __name__ == "__main__":
    sys.exit(main())
