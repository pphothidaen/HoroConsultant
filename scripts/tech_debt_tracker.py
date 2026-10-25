#!/usr/bin/env python3
"""Tech Debt Tracker - Computes and tracks technical debt metrics over time."""

import argparse
import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import ast
import hashlib


class TechDebtAnalyzer:
    """Analyzes codebase for technical debt metrics."""
    
    def __init__(self, path: str):
        self.path = Path(path)
        self.history_file = Path(".hermes/tech_debt_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def analyze(self) -> Dict:
        """Run full tech debt analysis."""
        if self.path.is_file():
            files = [self.path]
        else:
            files = list(self.path.rglob("*.py"))
            # Filter out unwanted directories
            files = [f for f in files if not any(
                part.startswith('.') or part in ('venv', 'env', '__pycache__', '.git', 'node_modules')
                for part in f.parts
            )]
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "path": str(self.path),
            "files_analyzed": len(files),
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "complexity": {
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "duplication": {
                "potential_duplicates": 0,
                "duplicate_blocks": []
            },
            "maintainability": {
                "avg_function_length": 0,
                "long_functions": [],
                "large_classes": []
            },
            "coverage_gaps": {
                "untested_files": [],
                "low_coverage_functions": []
            },
            "outdated_patterns": {
                "old_style_classes": 0,
                "bare_excepts": 0,
                "mutable_defaults": 0
            },
            "hotspots": [],
            "summary_score": 0
        }
        
        function_lengths = []
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                metrics["total_lines"] += len(lines)
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        metrics["total_functions"] += 1
                        func_length = (node.end_lineno - node.lineno) if (hasattr(node, 'end_lineno') and node.end_lineno is not None) else 0
                        function_lengths.append(func_length)
                        
                        if func_length > 50:
                            metrics["maintainability"]["long_functions"].append({
                                "file": str(file_path),
                                "function": node.name,
                                "lines": func_length,
                                "line_start": node.lineno
                            })
                        
                        # Check for complexity indicators
                        complexity = self._estimate_complexity(node)
                        if complexity > 10:
                            metrics["complexity"]["high"] += 1
                        elif complexity > 5:
                            metrics["complexity"]["medium"] += 1
                        else:
                            metrics["complexity"]["low"] += 1
                        
                        # Check for mutable defaults
                        for default in node.args.defaults:
                            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                metrics["outdated_patterns"]["mutable_defaults"] += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        metrics["total_classes"] += 1
                        # Check for old-style classes (no explicit inheritance in Python 2 style)
                        if not node.bases and hasattr(node, 'keywords'):
                            pass  # Python 3 classes are new-style by default
                        
                        # Large classes
                        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                        if len(methods) > 20:
                            metrics["maintainability"]["large_classes"].append({
                                "file": str(file_path),
                                "class": node.name,
                                "methods": len(methods),
                                "line_start": node.lineno
                            })
                    
                    elif isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            metrics["outdated_patterns"]["bare_excepts"] += 1
                
            except Exception as e:
                print(f"Warning: Could not analyze {file_path}: {e}", file=sys.stderr)
        
        # Calculate averages
        if function_lengths:
            metrics["maintainability"]["avg_function_length"] = round(sum(function_lengths) / len(function_lengths), 1)
        
        # Identify hotspots
        metrics["hotspots"] = self._identify_hotspots(files, metrics)
        
        # Calculate summary score (0-100, lower is better)
        metrics["summary_score"] = self._calculate_score(metrics)
        
        return metrics
    
    def _estimate_complexity(self, node: ast.FunctionDef) -> int:
        """Estimate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _identify_hotspots(self, files: List[Path], metrics: Dict) -> List[Dict]:
        """Identify files with high debt + high churn potential."""
        hotspots = []
        
        # Files with long functions
        for lf in metrics["maintainability"]["long_functions"]:
            hotspots.append({
                "file": lf["file"],
                "reason": f"Long function: {lf['function']} ({lf['lines']} lines)",
                "severity": "high" if lf["lines"] > 100 else "medium",
                "metric": "function_length"
            })
        
        # Files with high complexity
        if metrics["complexity"]["high"] > 0:
            # Would need per-file tracking for precise hotspots
            pass
        
        # Files with many issues
        for lc in metrics["maintainability"]["large_classes"]:
            hotspots.append({
                "file": lc["file"],
                "reason": f"Large class: {lc['class']} ({lc['methods']} methods)",
                "severity": "medium",
                "metric": "class_size"
            })
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        hotspots.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return hotspots[:10]  # Top 10
    
    def _calculate_score(self, metrics: Dict) -> int:
        """Calculate debt score (0-100, lower is better)."""
        score = 0
        
        # Complexity penalty
        score += metrics["complexity"]["high"] * 10
        score += metrics["complexity"]["medium"] * 5
        
        # Long functions penalty
        score += len(metrics["maintainability"]["long_functions"]) * 3
        
        # Large classes penalty
        score += len(metrics["maintainability"]["large_classes"]) * 5
        
        # Outdated patterns penalty
        score += metrics["outdated_patterns"]["bare_excepts"] * 2
        score += metrics["outdated_patterns"]["mutable_defaults"] * 3
        
        # Cap at 100
        return min(score, 100)
    
    def update_history(self, metrics: Dict):
        """Update history file with new metrics."""
        history = []
        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text())
            except Exception:
                history = []
        
        # Keep only last 50 entries
        history.append(metrics)
        history = history[-50:]
        
        self.history_file.write_text(json.dumps(history, indent=2))
    
    def show_history(self) -> Dict:
        """Show historical trends."""
        if not self.history_file.exists():
            return {"error": "No history found", "entries": []}
        
        try:
            history = json.loads(self.history_file.read_text())
        except Exception:
            return {"error": "Could not read history", "entries": []}
        
        if not history:
            return {"entries": []}
        
        # Calculate trends
        latest = history[-1]
        trends = {
            "entries": history,
            "latest_score": latest.get("summary_score", 0),
            "score_trend": "stable"
        }
        
        if len(history) >= 2:
            prev_score = history[-2].get("summary_score", 0)
            curr_score = latest.get("summary_score", 0)
            if curr_score > prev_score + 5:
                trends["score_trend"] = "worsening"
            elif curr_score < prev_score - 5:
                trends["score_trend"] = "improving"
        
        return trends


def main():
    parser = argparse.ArgumentParser(description="Tech Debt Tracker - Track technical debt metrics")
    parser.add_argument("--path", default=".", help="Path to analyze (file or directory)")
    parser.add_argument("--output", choices=["json", "text"], default="text", help="Output format")
    parser.add_argument("--update-history", action="store_true", help="Save metrics to history")
    parser.add_argument("--show-history", action="store_true", help="Show historical trends")
    args = parser.parse_args()
    
    analyzer = TechDebtAnalyzer(args.path)
    
    if args.show_history:
        result = analyzer.show_history()
    else:
        result = analyzer.analyze()
        if args.update_history:
            analyzer.update_history(result)
    
    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        if "error" in result:
            print(f"❌ {result['error']}")
        elif args.show_history:
            print(f"📊 Tech Debt History ({len(result['entries'])} entries)")
            print(f"Latest Score: {result['latest_score']}/100")
            print(f"Trend: {result['score_trend'].upper()}")
            print()
            for entry in result['entries'][-5:]:
                ts = entry.get('timestamp', 'unknown')[:19].replace('T', ' ')
                score = entry.get('summary_score', 0)
                files = entry.get('files_analyzed', 0)
                print(f"  {ts} | Score: {score}/100 | Files: {files}")
        else:
            print(f"📊 Tech Debt Analysis: {args.path}")
            print(f"{'='*50}")
            print(f"Files analyzed: {result['files_analyzed']}")
            print(f"Total lines: {result['total_lines']}")
            print(f"Functions: {result['total_functions']}")
            print(f"Classes: {result['total_classes']}")
            print(f"Avg function length: {result['maintainability']['avg_function_length']} lines")
            print(f"Summary Score: {result['summary_score']}/100 (lower is better)")
            print()
            
            print("Complexity:")
            for level, count in result['complexity'].items():
                print(f"  {level.capitalize()}: {count}")
            
            print()
            print("Outdated Patterns:")
            for pattern, count in result['outdated_patterns'].items():
                if count > 0:
                    print(f"  {pattern.replace('_', ' ').title()}: {count}")
            
            print()
            print("Maintainability Issues:")
            if result['maintainability']['long_functions']:
                print(f"  Long functions (>50 lines): {len(result['maintainability']['long_functions'])}")
            if result['maintainability']['large_classes']:
                print(f"  Large classes (>20 methods): {len(result['maintainability']['large_classes'])}")
            
            print()
            print("Top Hotspots:")
            for i, hs in enumerate(result['hotspots'][:5], 1):
                print(f"  {i}. {hs['file']} - {hs['reason']} [{hs['severity']}]")
            
            if not result['hotspots']:
                print("  None identified")
    
    sys.exit(0)


if __name__ == "__main__":
    main()