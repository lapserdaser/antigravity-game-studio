#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverse-GDD Scanner
Fast, token-free AST & regex analyzer that extracts game mechanics, architecture,
export parameters, scene hierarchies, signals, and TODO items from codebases.
"""

import os
import sys
import json
import re
from pathlib import Path

IGNORE_DIRS = {
    ".git", ".godot", ".import", "node_modules", ".venv", "venv", "env",
    "bin", "obj", "dist", "build", ".vs", ".vscode", ".idea", "__pycache__"
}

CODE_EXTENSIONS = {".gd", ".cs", ".py", ".lua", ".luau", ".ts", ".js", ".cpp", ".hpp", ".h"}
SCENE_EXTENSIONS = {".tscn"}

def read_text_safe(path):
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    return ""

def parse_gdscript(content, rel_path):
    data = {
        "file": rel_path,
        "class_name": None,
        "extends": None,
        "exports": [],
        "signals": [],
        "methods": [],
        "todos": []
    }
    
    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # TODO / FIXME
        todo_match = re.search(r"#\s*(TODO|FIXME|HACK|NOTE):\s*(.+)", stripped, re.IGNORECASE)
        if todo_match:
            data["todos"].append({
                "line": idx,
                "type": todo_match.group(1).upper(),
                "text": todo_match.group(2).strip()
            })
            
        # class_name
        cn_match = re.match(r"^class_name\s+([A-Za-z0-9_]+)", stripped)
        if cn_match:
            data["class_name"] = cn_match.group(1)
            
        # extends
        ext_match = re.match(r"^extends\s+([A-Za-z0-9_\"/.]+)", stripped)
        if ext_match:
            data["extends"] = ext_match.group(1).replace('"', '')
            
        # @export
        exp_match = re.match(r"^@export(?:_range|_group|_subgroup|_file|_enum|_flags[^\)]*)?\s+var\s+([A-Za-z0-9_]+)(?:\s*:\s*([^=]+))?(?:\s*=\s*(.+))?", stripped)
        if exp_match:
            data["exports"].append({
                "name": exp_match.group(1),
                "type": (exp_match.group(2) or "Variant").strip(),
                "default": (exp_match.group(3) or "").strip()
            })
            
        # signal
        sig_match = re.match(r"^signal\s+([A-Za-z0-9_]+)(?:\((.*?)\))?", stripped)
        if sig_match:
            data["signals"].append({
                "name": sig_match.group(1),
                "params": (sig_match.group(2) or "").strip()
            })
            
        # func
        func_match = re.match(r"^func\s+([A-Za-z0-9_]+)\s*\((.*?)\)", stripped)
        if func_match:
            func_name = func_match.group(1)
            if not func_name.startswith("_") or func_name in ("_ready", "_process", "_physics_process", "_unhandled_input"):
                data["methods"].append({
                    "name": func_name,
                    "params": func_match.group(2).strip()
                })
                
    if not data["class_name"]:
        # Fallback to filename as class identifier
        data["class_name"] = Path(rel_path).stem
        
    return data

def parse_csharp(content, rel_path):
    data = {
        "file": rel_path,
        "class_name": Path(rel_path).stem,
        "extends": None,
        "exports": [],
        "signals": [],
        "methods": [],
        "todos": []
    }
    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        todo_match = re.search(r"//\s*(TODO|FIXME|HACK|NOTE):\s*(.+)", stripped, re.IGNORECASE)
        if todo_match:
            data["todos"].append({
                "line": idx,
                "type": todo_match.group(1).upper(),
                "text": todo_match.group(2).strip()
            })
            
        class_match = re.search(r"(?:public|internal)?\s*(?:partial\s+)?class\s+([A-Za-z0-9_]+)(?:\s*:\s*([A-Za-z0-9_,\s]+))?", stripped)
        if class_match:
            data["class_name"] = class_match.group(1)
            if class_match.group(2):
                data["extends"] = class_match.group(2).strip().split(",")[0].strip()
                
        # [Export]
        if "[Export" in stripped or "[SerializeField]" in stripped:
            # find next line or same line variable
            var_match = re.search(r"(?:public|private|protected)\s+([A-Za-z0-9_<>\[\]]+)\s+([A-Za-z0-9_]+)(?:\s*=\s*(.+?);)?", stripped)
            if var_match:
                data["exports"].append({
                    "name": var_match.group(2),
                    "type": var_match.group(1),
                    "default": (var_match.group(3) or "").strip()
                })
    return data

def parse_tscn(content, rel_path):
    scene_info = {
        "file": rel_path,
        "name": Path(rel_path).stem,
        "root_type": None,
        "script": None,
        "nodes": []
    }
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[node name="):
            match = re.search(r'name="([^"]+)"\s+type="([^"]+)"', stripped)
            if match:
                node_name = match.group(1)
                node_type = match.group(2)
                if not scene_info["root_type"] and 'parent=".' not in stripped and 'parent=' not in stripped:
                    scene_info["root_type"] = node_type
                scene_info["nodes"].append({"name": node_name, "type": node_type})
        elif "ext_resource" in stripped and "path=" in stripped and (".gd" in stripped or ".cs" in stripped):
            script_match = re.search(r'path="([^"]+)"', stripped)
            if script_match and not scene_info["script"]:
                scene_info["script"] = script_match.group(1)
    return scene_info

def scan_project(root_dir):
    root_path = Path(root_dir).resolve()
    manifest = {
        "project_root": str(root_path),
        "total_files": 0,
        "modules": [],
        "scenes": [],
        "all_todos": []
    }
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        
        for file in filenames:
            ext = Path(file).suffix.lower()
            full_path = Path(dirpath) / file
            rel_path = str(full_path.relative_to(root_path)).replace("\\", "/")
            
            if ext in CODE_EXTENSIONS:
                manifest["total_files"] += 1
                content = read_text_safe(full_path)
                if not content:
                    continue
                if ext == ".gd":
                    mod = parse_gdscript(content, rel_path)
                    manifest["modules"].append(mod)
                    manifest["all_todos"].extend([{**t, "file": rel_path} for t in mod["todos"]])
                elif ext == ".cs":
                    mod = parse_csharp(content, rel_path)
                    manifest["modules"].append(mod)
                    manifest["all_todos"].extend([{**t, "file": rel_path} for t in mod["todos"]])
                else:
                    # Generic
                    todos = []
                    for idx, line in enumerate(content.splitlines(), start=1):
                        m = re.search(r"(?:#|//)\s*(TODO|FIXME):\s*(.+)", line, re.IGNORECASE)
                        if m:
                            todos.append({"line": idx, "type": m.group(1).upper(), "text": m.group(2).strip(), "file": rel_path})
                    manifest["all_todos"].extend(todos)
            elif ext in SCENE_EXTENSIONS:
                content = read_text_safe(full_path)
                if content:
                    manifest["scenes"].append(parse_tscn(content, rel_path))
                    
    return manifest

def main():
    if len(sys.argv) < 2:
        print("Usage: python scan_project.py <path_to_project> [output_json_path]")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else "reverse_gdd_manifest.json"
    
    manifest = scan_project(target_dir)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    print(f"SUCCESS: Scanned {manifest['total_files']} code files and {len(manifest['scenes'])} scenes.")
    print(f"Discovered {len(manifest['modules'])} modules and {len(manifest['all_todos'])} TODO items.")
    print(f"Manifest written to: {out_file}")

if __name__ == "__main__":
    main()
