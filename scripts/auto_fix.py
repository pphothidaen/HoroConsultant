#!/usr/bin/env python3
"""Auto-Fix Engine - Safely applies trivial fixes (formatting, imports, simple patterns)."""

import argparse
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import ast
import re


class AutoFixer:
    """Applies safe automatic fixes to Python files."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.fixes_skipped = []
    
    def fix_file(self, file_path: str) -> bool:
        """Fix a single Python file. Returns True if any changes made."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            print(f"File not found: {file_path}", file=sys.stderr)
            return False
        
        if path.suffix != '.py':
            print(f"Only Python files supported: {file_path}", file=sys.stderr)
            return False
        
        original = path.read_text(encoding='utf-8')
        fixed = original
        
        # Apply fixes in order
        fixed = self._fix_formatting(fixed)
        fixed = self._fix_imports(fixed)
        fixed = self._fix_whitespace(fixed)
        fixed = self._fix_unused_imports(fixed, path)
        fixed = self._fix_trailing_commas(fixed)
        
        if fixed != original:
            self.fixes_applied.append({
                "file": str(path),
                "changes": self._diff(original, fixed)
            })
            if not self.dry_run:
                path.write_text(fixed, encoding='utf-8')
                print(f"✅ Fixed: {file_path}")
            else:
                print(f"🔍 Would fix: {file_path}")
            return True
        else:
            print(f"✨ No changes needed: {file_path}")
            return False
    
    def _fix_formatting(self, code: str) -> str:
        """Apply black formatting via subprocess."""
        try:
            result = subprocess.run(
                ["python3", "-m", "black", "--quiet", "-"],
                input=code, text=True, capture_output=True, check=False
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        return code
    
    def _fix_imports(self, code: str) -> str:
        """Apply isort for import sorting."""
        try:
            result = subprocess.run(
                ["python3", "-m", "isort", "--quiet", "-"],
                input=code, text=True, capture_output=True, check=False
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        return code
    
    def _fix_whitespace(self, code: str) -> str:
        """Fix basic whitespace issues."""
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            # Fix multiple blank lines (max 2)
            fixed_lines.append(line)
        
        # Join and fix multiple blank lines
        result = '\n'.join(fixed_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        # Ensure file ends with newline
        if result and not result.endswith('\n'):
            result += '\n'
        return result
    
    def _fix_unused_imports(self, code: str, file_path: Path) -> str:
        """Remove unused imports (basic detection)."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code
        
        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name.split('.')[0], node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append((node.module.split('.')[0], node.lineno))
        
        # Find all names used in code
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)
        
        # Check which imports might be unused (simple heuristic)
        lines = code.split('\n')
        for imp_name, line_no in imports:
            if imp_name not in used_names and imp_name not in ('os', 'sys', 'json', 'typing', 'pathlib', 'dataclasses'):
                # Comment out potentially unused import
                if 0 < line_no <= len(lines):
                    line = lines[line_no - 1]
                    if line.strip().startswith(('import ', 'from ')) and imp_name in line:
                        # Be conservative - just note it
                        self.fixes_skipped.append(f"Potential unused import '{imp_name}' at line {line_no} in {file_path}")
        
        return code
    
    def _fix_trailing_commas(self, code: str) -> str:
        """Add trailing commas where appropriate (for multi-line structures)."""
        # This is complex to do correctly without black, so skip for now
        return code
    
    def _diff(self, original: str, fixed: str) -> List[str]:
        """Generate a simple diff."""
        import difflib
        diff = list(difflib.unified_diff(
            original.split('\n'), fixed.split('\n'),
            lineterm='', n=3
        ))
        return diff[2:] if len(diff) > 2 else []
    
    def get_summary(self) -> Dict:
        """Get summary of fixes."""
        return {
            "files_changed": len(self.fixes_applied),
            "details": self.fixes_applied,
            "skipped": self.fixes_skipped
        }


def fix_directory(dir_path: str, dry_run: bool = False) -> Dict:
    """Fix all Python files in a directory."""
    fixer = AutoFixer(dry_run=dry_run)
    path = Path(dir_path)
    
    if path.is_file():
        fixer.fix_file(str(path))
    elif path.is_dir():
        for py_file in path.rglob("*.py"):
            # Skip virtual environments and hidden dirs
            if any(part.startswith('.') or part in ('venv', 'env', '__pycache__', '.git') 
                   for part in py_file.parts):
                continue
            fixer.fix_file(str(py_file))
    
    return fixer.get_summary()


def main():
    parser = argparse.ArgumentParser(description="Auto-Fix Engine - Safe automatic code fixes")
    parser.add_argument("--file", help="Single file to fix")
    parser.add_argument("--dir", help="Directory to fix (recursive)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without applying")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (default if not dry-run)")
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.error("Must specify --file or --dir")
    
    dry_run = args.dry_run or not args.apply
    
    if args.file:
        summary = fix_directory(args.file, dry_run)
    else:
        summary = fix_directory(args.dir, dry_run)
    
    if args.output == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"Auto-Fix Summary ({'DRY RUN' if dry_run else 'APPLIED'})")
        print(f"{'='*50}")
        print(f"Files changed: {summary['files_changed']}")
        for fix in summary['details']:
            print(f"  📝 {fix['file']}")
            for change in fix['changes'][:5]:
                print(f"    {change}")
            if len(fix['changes']) > 5:
                print(f"    ... and {len(fix['changes']) - 5} more changes")
        if summary['skipped']:
            print(f"\nSkipped/Noted: {len(summary['skipped'])}")
            for skip in summary['skipped'][:3]:
                print(f"  ⚠️ {skip}")
    
    sys.exit(0)


if __name__ == "__main__":
    import json
    main()