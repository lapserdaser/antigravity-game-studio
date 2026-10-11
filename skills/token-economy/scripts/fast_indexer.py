#!/usr/bin/env python3
"""
Zero-Token Fast Codebase Scanner for PROJECT_INDEX.md generation.
Scans source files (Python, JS/TS/JSX/TSX, GDScript, C#, Luau) and outputs
compact AST/structural signatures without dumping file contents.
"""
import os
import sys
import ast
import re
import argparse
from pathlib import Path

IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", "__pycache__", ".godot", 
    "addons", ".import", ".gemini", "vendor", "bin", "obj", ".next", 
    ".venv", "venv", "env", ".idea", ".vscode", "uploads", "data"
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".mp3", 
    ".wav", ".ogg", ".db", ".sqlite", ".sqlite3", ".log", ".lock", 
    ".map", ".min.js", ".min.css", ".exe", ".dll", ".pck"
}

def scan_python(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=str(path))
        classes = []
        funcs = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                classes.append(f"{node.name}({', '.join(bases)})" if bases else node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append(node.name)
        return classes, funcs
    except Exception:
        return [], []

def scan_js_ts(path):
    classes = []
    funcs = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for m in re.finditer(r"(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_]+)", content):
            classes.append(m.group(1))
        for m in re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)", content):
            funcs.append(m.group(1))
        for m in re.finditer(r"(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", content):
            funcs.append(m.group(1))
    except Exception:
        pass
    return classes, funcs[:12]

def scan_gdscript(path):
    classes = []
    funcs = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("class_name "):
                    classes.append(line.split()[1])
                elif line.startswith("extends "):
                    classes.append(f"extends {line.split()[1]}")
                elif line.startswith("func ") and "(" in line:
                    fname = line.split("func ")[1].split("(")[0].strip()
                    if not fname.startswith("_"):
                        funcs.append(fname)
    except Exception:
        pass
    return classes, funcs[:10]

def scan_csharp(path):
    classes = []
    funcs = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for m in re.finditer(r"(?:public|internal)\s+(?:class|interface|struct)\s+([A-Za-z0-9_]+)", content):
            classes.append(m.group(1))
        for m in re.finditer(r"(?:public|protected)\s+(?:async\s+)?(?:void|[A-Za-z0-9_<>]+)\s+([A-Za-z0-9_]+)\s*\(", content):
            fn = m.group(1)
            if fn not in {"if", "for", "foreach", "while", "switch", "catch"}:
                funcs.append(fn)
    except Exception:
        pass
    return classes, funcs[:10]

def main():
    parser = argparse.ArgumentParser(description="Fast Codebase Indexer")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    print(f"=== PROJECT SCAN: {root_path.name} ({root_path}) ===")

    file_count = 0
    modules = {}

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(root_path)
        
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in IGNORE_EXTENSIONS or file.startswith("."):
                continue
            
            full_path = Path(root) / file
            rel_file = full_path.relative_to(root_path)
            
            classes, funcs = [], []
            if ext == ".py":
                classes, funcs = scan_python(full_path)
            elif ext in {".js", ".jsx", ".ts", ".tsx"}:
                classes, funcs = scan_js_ts(full_path)
            elif ext == ".gd":
                classes, funcs = scan_gdscript(full_path)
            elif ext == ".cs":
                classes, funcs = scan_csharp(full_path)
            
            parts = rel_file.parts
            top_mod = parts[0] if len(parts) > 1 else "root"
            if top_mod not in modules:
                modules[top_mod] = []
                
            modules[top_mod].append({
                "path": str(rel_file).replace("\\", "/"),
                "classes": classes,
                "funcs": funcs
            })
            file_count += 1

    for mod, flist in modules.items():
        print(f"\n[{mod.upper()}] ({len(flist)} files):")
        for item in flist:
            details = []
            if item["classes"]:
                details.append(f"classes: {item['classes']}")
            if item["funcs"]:
                details.append(f"funcs: {item['funcs']}")
            info_str = f" ({'; '.join(details)})" if details else ""
            print(f"  - {item['path']}{info_str}")

    print(f"\nTotal scanned files: {file_count}")

if __name__ == "__main__":
    main()
