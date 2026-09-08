"""
Fast Repository Scanner for Project Indexing (Zero-LLM Token Scanner)
Scans codebase structure, extracts high-level signatures, classes, and signals.
Outputs a clean outline for generating PROJECT_INDEX.md without reading file bodies via LLM.
"""
import os
import sys
import re

IGNORE_DIRS = {
    '.git', '.godot', '.import', 'node_modules', 'dist', 'build', 
    'venv', '__pycache__', '.vscode', '.idea', 'addons', 'bin',
    'obj', 'target', '.system_generated', 'logs'
}

VALID_EXTENSIONS = {
    '.gd', '.ts', '.js', '.jsx', '.tsx', 
    '.cs', '.py', '.luau', '.lua', '.cpp', '.h', '.hpp'
}

def scan_project(root_path="."):
    summary = []
    total_files = 0
    
    for root, dirs, files in os.walk(root_path):
        # Exclude blacklisted directories and hidden folders
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]
        
        rel_dir = os.path.relpath(root, root_path).replace('\\', '/')
        if rel_dir == ".":
            rel_dir = "root"
            
        code_files = [f for f in files if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS]
        if not code_files:
            continue
            
        summary.append(f"\n### 📁 {rel_dir}")
        
        for file in code_files:
            total_files += 1
            file_path = os.path.join(root, file)
            signatures = []
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line_clean = line.strip()
                        # Detect key declarations (GDScript, Python, TypeScript, C#, Luau)
                        if re.match(r'^(class_name|extends|export|signal|class\s|interface\s|enum\s|def\s|function\s|public\sclass)', line_clean):
                            # Skip internal helpers and comments
                            if not line_clean.startswith(('def _', 'private', '//', '#')):
                                sig = line_clean.split('(')[0].replace('{', '').replace(':', '').strip()
                                signatures.append(sig)
                        if len(signatures) >= 4:
                            break
            except Exception:
                pass
                
            sig_str = f" → `{' | '.join(signatures[:3])}`" if signatures else ""
            summary.append(f"* `{file}`{sig_str}")
            
    header = f"# Codebase Outline ({total_files} files scanned)\n"
    return header + "\n".join(summary)

if __name__ == "__main__":
    target_path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(scan_project(target_path))
