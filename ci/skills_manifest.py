#!/usr/bin/env python3
"""List deployable skills and their Hermes category from each SKILL.md frontmatter.

Prints one tab-separated line per skill:  <skill_dir>\t<category>\t<skill_name>

The deploy workflow uses this to place each skill at
<profile-skills-root>/<category>/<name>, so the flat repo layout (skills/<name>/)
maps to the profile's category layout (skills/<category>/<name>/) without a
hand-maintained path per skill. Add a skill folder with a category in its
frontmatter and it is picked up automatically.

Pure stdlib; no PyYAML. Reads the single `category:` key inside the YAML
frontmatter block. Exits non-zero if any skill lacks a category.
"""
import os
import re
import sys

SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")
)


def frontmatter_lines(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        out.append(line)
    return []  # no closing fence -> not valid frontmatter


def category_of(skill_md):
    for line in frontmatter_lines(skill_md):
        m = re.match(r"\s*category:\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


def main():
    rc = 0
    for name in sorted(os.listdir(SKILLS_DIR)):
        d = os.path.join(SKILLS_DIR, name)
        skill_md = os.path.join(d, "SKILL.md")
        if not os.path.isdir(d) or not os.path.exists(skill_md):
            continue
        cat = category_of(skill_md)
        if not cat:
            print(
                f"ERROR: {name}: no metadata.hermes.category in SKILL.md",
                file=sys.stderr,
            )
            rc = 1
            continue
        print(f"{d}\t{cat}\t{name}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
