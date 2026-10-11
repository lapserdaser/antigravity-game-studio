#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zero-Hardcode & Rich Inspector Auditor for Godot 4 (GDScript).
Checks scripts for hardcoded paths, raw string get_node, missing @export_group,
and bare unconstrained exports.
"""

import sys
import os
import re
from pathlib import Path

# Regular expressions for audit
RE_PRELOAD_RES = re.compile(r'\b(preload|load)\s*\(\s*["\']res://', re.IGNORECASE)
RE_GET_NODE_PATH = re.compile(r'\bget_node\s*\(\s*["\'](?![%])([^"\']+)["\']\)', re.IGNORECASE)
RE_SLASH_DOLLAR = re.compile(r'(?<!\w)\$["\']?([a-zA-Z0-9_]+/[a-zA-Z0-9_/]+)["\']?')
RE_EXPORT_LINE = re.compile(r'^\s*@export\b')
RE_EXPORT_GROUP = re.compile(r'^\s*@export_group\b')
RE_BARE_NUMERIC_EXPORT = re.compile(r'^\s*@export\s+var\s+\w+\s*:\s*(float|int)\b')

def audit_file(filepath: Path) -> list[str]:
    violations = []
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return [f"ERROR: Could not read {filepath}: {e}"]

    export_count = 0
    has_export_group = False
    
    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        
        # Skip pure comments and empty lines
        if not line or line.startswith("#"):
            continue
            
        # Strip trailing inline comments for regex matching
        code_part = raw_line.split("#")[0].strip()

        # 1. Check preload/load res://
        if RE_PRELOAD_RES.search(code_part):
            violations.append(
                f"Line {idx}: [HARDCODE] String resource path found in '{code_part}'. "
                f"Replace with '@export var ...: ResourceType' (AudioStream, PackedScene, Texture2D)."
            )

        # 2. Check get_node with path
        match_get_node = RE_GET_NODE_PATH.search(code_part)
        if match_get_node:
            violations.append(
                f"Line {idx}: [HARDCODE] String get_node('{match_get_node.group(1)}') found. "
                f"Use '@export var ...: Node' or Scene Unique Node (%UniqueName)."
            )

        # 3. Check $A/B nested paths
        match_dollar = RE_SLASH_DOLLAR.search(code_part)
        if match_dollar and not match_dollar.group(1).startswith("%"):
            violations.append(
                f"Line {idx}: [FRAGILE_PATH] Nested node path '${match_dollar.group(1)}' found. "
                f"Use Scene Unique Node (%{match_dollar.group(1).split('/')[-1]}) or '@export var ...: Node'."
            )

        # Count exports & check group
        if RE_EXPORT_GROUP.search(line):
            has_export_group = True
        elif RE_EXPORT_LINE.search(line):
            export_count += 1
            if RE_BARE_NUMERIC_EXPORT.search(line):
                violations.append(
                    f"Line {idx}: [POOR_INSPECTOR] Bare numeric export '{line}'. "
                    f"Use '@export_range(min, max, step, \"suffix\")' for inspector slider and unit."
                )

    # 4. Check if multiple exports exist without any grouping
    if export_count >= 3 and not has_export_group:
        violations.append(
            f"File has {export_count} exported variables but NO '@export_group' category. "
            f"Add '@export_group(\"Category Name\", \"prefix_\")' to keep Inspector organized."
        )

    return violations

def main():
    if len(sys.argv) < 2:
        print("Usage: python audit_zero_hardcode.py <path_to_file_or_directory>")
        sys.exit(1)

    target_path = Path(sys.argv[1])
    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}")
        sys.exit(1)

    files_to_check = []
    if target_path.is_file():
        if target_path.suffix == ".gd":
            files_to_check.append(target_path)
        else:
            print(f"Skipping non-gd file: {target_path}")
            sys.exit(0)
    else:
        files_to_check = list(target_path.rglob("*.gd"))

    if not files_to_check:
        print(f"No .gd files found in {target_path}")
        sys.exit(0)

    total_violations = 0
    print(f"=== Zero-Hardcode & Rich Inspector Audit ({len(files_to_check)} files) ===")

    for file in files_to_check:
        violations = audit_file(file)
        if violations:
            total_violations += len(violations)
            print(f"\n[FAIL] {file}:")
            for v in violations:
                print(f"  - {v}")
        else:
            print(f"[PASS] {file.name}")

    print("\n--------------------------------------------------")
    if total_violations == 0:
        print("RESULT: ALL SCRIPTS PASSED! Zero hardcode, clean inspector.")
        sys.exit(0)
    else:
        print(f"RESULT: FAILED! Found {total_violations} architectural violation(s).")
        sys.exit(1)

if __name__ == "__main__":
    main()
