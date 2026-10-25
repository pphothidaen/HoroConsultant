#!/usr/bin/env python3
"""
Documentation Sync (KAN-308 4D)
- Doc/code drift detection (docstrings, README, API docs vs code)
- API docs generation from OpenAPI/FastAPI specs
- Architecture diagram sync (mermaid/excalidraw validation)
- Code example validation (execute examples in docs)
"""
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class DocstringExtractor:
    """Extract docstrings from Python source code"""

    @staticmethod
    def extract_from_file(file_path: Path) -> Dict[str, str]:
        """Extract all docstrings from a Python file"""
        try:
            source = file_path.read_text()
            tree = ast.parse(source)
            docstrings = {}

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        docstrings[node.name] = docstring.strip()

            # Also get module-level docstring
            module_doc = ast.get_docstring(tree)
            if module_doc:
                docstrings["__module__"] = module_doc.strip()

            return docstrings
        except Exception:
            return {}

    @staticmethod
    def extract_from_dir(dir_path: Path, pattern: str = "*.py") -> Dict[str, Dict[str, str]]:
        """Extract docstrings from all Python files in directory"""
        result = {}
        for py_file in dir_path.rglob(pattern):
            if "__pycache__" not in str(py_file):
                docstrings = DocstringExtractor.extract_from_file(py_file)
                if docstrings:
                    rel_path = py_file.relative_to(dir_path)
                    result[str(rel_path)] = docstrings
        return result


class DriftDetector:
    """Detect drift between documentation and code"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.extractor = DocstringExtractor()

    def check_python_docstrings(self) -> List[Dict]:
        """Check for outdated docstrings in .md files vs code"""
        issues = []

        # Get all Python docstrings
        code_docstrings = self.extractor.extract_from_dir(self.project_root)

        # Check markdown files for references to functions/classes
        for md_file in self.project_root.rglob("*.md"):
            if ".git" in str(md_file) or ".pytest_cache" in str(md_file):
                continue
            content = md_file.read_text()

            # Look for function/class references in markdown
            # Pattern: `function_name` or **function_name** or function_name()
            refs = re.findall(r'[`*](\w+)[`*]|(\w+)\(\)', content)
            refs = [r[0] or r[1] for r in refs if r[0] or r[1]]

            for ref in set(refs):
                # Check if this exists in code
                found = False
                for file_docstrings in code_docstrings.values():
                    if ref in file_docstrings:
                        found = True
                        break

                if not found and len(ref) > 3:  # Ignore short refs
                    issues.append({
                        "type": "missing_in_code",
                        "file": str(md_file.relative_to(self.project_root)),
                        "reference": ref,
                        "message": f"Reference '{ref}' in docs not found in code"
                    })

        return issues

    def check_readme_vs_code(self) -> List[Dict]:
        """Check README for outdated API documentation"""
        issues = []
        readme = self.project_root / "README.md"
        if not readme.exists():
            return issues

        content = readme.read_text()

        # Check for API sections that reference functions
        api_section = re.search(r'(?:##\s*API|##\s*Reference)(.*?)(?:##|\Z)', content, re.DOTALL | re.IGNORECASE)
        if api_section:
            api_content = api_section.group(1)
            # Look for function signatures
            funcs = re.findall(r'(\w+)\([^)]*\)\s*->\s*\w+', api_content)
            for func in funcs:
                # Check if function exists in code
                found = False
                for file_docstrings in self.extractor.extract_from_dir(self.project_root).values():
                    if func in file_docstrings:
                        found = True
                        break
                if not found:
                    issues.append({
                        "type": "readme_api_drift",
                        "file": "README.md",
                        "reference": func,
                        "message": f"API function '{func}' in README not found in code"
                    })

        return issues

    def check_openapi_vs_implementation(self, openapi_path: Path) -> List[Dict]:
        """Check OpenAPI spec vs actual implementation"""
        issues = []
        if not openapi_path.exists():
            return issues

        try:
            spec = json.loads(openapi_path.read_text())
            paths = spec.get("paths", {})

            # This is a simplified check - in reality would need to match routes to handlers
            for path, methods in paths.items():
                for method, details in methods.items():
                    if isinstance(details, dict):
                        summary = details.get("summary", "")
                        if summary and "TODO" in summary.upper():
                            issues.append({
                                "type": "openapi_todo",
                                "file": str(openapi_path.relative_to(self.project_root)),
                                "path": path,
                                "method": method,
                                "message": f"OpenAPI {method.upper()} {path} has TODO in summary"
                            })
        except Exception as e:
            issues.append({
                "type": "openapi_parse_error",
                "file": str(openapi_path.relative_to(self.project_root)),
                "message": f"Failed to parse OpenAPI spec: {e}"
            })

        return issues

    def run_all_checks(self, openapi_path: Optional[Path] = None) -> Dict:
        """Run all drift detection checks"""
        all_issues = []

        print("Checking Python docstrings...")
        all_issues.extend(self.check_python_docstrings())

        print("Checking README vs code...")
        all_issues.extend(self.check_readme_vs_code())

        if openapi_path:
            print("Checking OpenAPI vs implementation...")
            all_issues.extend(self.check_openapi_vs_implementation(openapi_path))

        return {
            "issues": all_issues,
            "count": len(all_issues),
            "passed": len(all_issues) == 0
        }


class APIDocGenerator:
    """Generate API documentation from OpenAPI/FastAPI specs"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def openapi_to_markdown(self, openapi_path: Path, output_path: Path) -> bool:
        """Convert OpenAPI spec to Markdown"""
        try:
            spec = json.loads(openapi_path.read_text())
            info = spec.get("info", {})
            paths = spec.get("paths", {})

            lines = [
                f"# {info.get('title', 'API Documentation')}",
                f"Version: {info.get('version', '1.0')}",
                f"Description: {info.get('description', '')}",
                "",
                "## Endpoints",
                ""
            ]

            for path, methods in paths.items():
                lines.append(f"### {path}")
                lines.append("")
                for method, details in methods.items():
                    if isinstance(details, dict):
                        summary = details.get("summary", "")
                        desc = details.get("description", "")
                        lines.append(f"#### {method.upper()} {path}")
                        if summary:
                            lines.append(f"{summary}")
                        if desc:
                            lines.append(f"{desc}")
                        lines.append("")

            output_path.write_text("\n".join(lines))
            return True
        except Exception as e:
            print(f"Error generating API docs: {e}")
            return False

    def generate_from_fastapi(self, module_path: str, output_path: Path) -> bool:
        """Generate OpenAPI spec from FastAPI app"""
        try:
            # Import the module and get the app
            spec = subprocess.run(
                [sys.executable, "-c", f"import {module_path}; import json; print(json.dumps({module_path}.app.openapi()))"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if spec.returncode == 0:
                openapi_data = json.loads(spec.stdout)
                output_path.write_text(json.dumps(openapi_data, indent=2))
                return True
        except Exception as e:
            print(f"Error generating from FastAPI: {e}")
        return False


class DiagramValidator:
    """Validate architecture diagrams (mermaid/excalidraw)"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate_mermaid(self, diagram_path: Path) -> Dict:
        """Validate mermaid diagram syntax"""
        try:
            content = diagram_path.read_text()
            # Basic syntax check - mermaid diagrams start with graph, sequenceDiagram, etc.
            valid_starts = ["graph", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram",
                           "journey", "gantt", "pie", "timeline", "mindmap"]

            first_line = content.strip().split("\n")[0].strip()
            is_valid = any(first_line.startswith(s) for s in valid_starts)

            # Check for common syntax issues
            issues = []
            if not is_valid:
                issues.append(f"Invalid mermaid diagram start: {first_line}")

            # Check for unclosed brackets
            if content.count("[") != content.count("]"):
                issues.append("Unclosed brackets in mermaid diagram")

            return {
                "file": str(diagram_path.relative_to(self.project_root)),
                "valid": len(issues) == 0,
                "issues": issues,
                "type": "mermaid"
            }
        except Exception as e:
            return {
                "file": str(diagram_path.relative_to(self.project_root)),
                "valid": False,
                "issues": [f"Failed to read/parse: {e}"],
                "type": "mermaid"
            }

    def validate_excalidraw(self, diagram_path: Path) -> Dict:
        """Validate excalidraw diagram (JSON format)"""
        try:
            content = diagram_path.read_text()
            data = json.loads(content)

            # Excalidraw files have specific structure
            valid = (
                isinstance(data, dict) and
                data.get("type") == "excalidraw" and
                "elements" in data and
                "appState" in data
            )

            issues = []
            if not valid:
                issues.append("Invalid excalidraw format")

            return {
                "file": str(diagram_path.relative_to(self.project_root)),
                "valid": valid,
                "issues": issues,
                "type": "excalidraw",
                "element_count": len(data.get("elements", [])) if valid else 0
            }
        except Exception as e:
            return {
                "file": str(diagram_path.relative_to(self.project_root)),
                "valid": False,
                "issues": [f"Failed to read/parse: {e}"],
                "type": "excalidraw"
            }

    def find_diagrams(self) -> List[Path]:
        """Find all diagram files in project"""
        diagrams = []
        for ext in [".mmd", ".mermaid", ".excalidraw", ".drawio"]:
            diagrams.extend(self.project_root.rglob(f"*{ext}"))
        return diagrams

    def validate_all(self) -> Dict:
        """Validate all diagrams in project"""
        diagrams = self.find_diagrams()
        results = []

        for diagram in diagrams:
            if diagram.suffix in [".mmd", ".mermaid"]:
                results.append(self.validate_mermaid(diagram))
            elif diagram.suffix in [".excalidraw", ".drawio"]:
                results.append(self.validate_excalidraw(diagram))

        return {
            "diagrams": results,
            "total": len(results),
            "valid": sum(1 for r in results if r["valid"]),
            "invalid": sum(1 for r in results if not r["valid"])
        }


class CodeExampleValidator:
    """Validate code examples in documentation"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def extract_code_blocks(self, md_file: Path) -> List[Dict]:
        """Extract fenced code blocks from markdown"""
        content = md_file.read_text()
        blocks = []

        # Find fenced code blocks with language
        pattern = r'```(\w+)\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        for lang, code in matches:
            if lang in ["python", "py", "bash", "sh", "javascript", "js", "typescript", "ts"]:
                blocks.append({
                    "language": lang,
                    "code": code.strip(),
                    "file": str(md_file.relative_to(self.project_root))
                })

        return blocks

    def validate_python_example(self, code: str, file: str) -> Dict:
        """Validate a Python code example by executing it"""
        # Create a temporary file and run it
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "file": file,
                "valid": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                "file": file,
                "valid": False,
                "error": "Execution timeout"
            }
        except Exception as e:
            return {
                "file": file,
                "valid": False,
                "error": str(e)
            }
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

    def validate_bash_example(self, code: str, file: str) -> Dict:
        """Validate a bash code example"""
        # For safety, only run simple commands - in practice might want sandbox
        try:
            result = subprocess.run(
                ["bash", "-c", code],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "file": file,
                "valid": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {"file": file, "valid": False, "error": "Execution timeout"}
        except Exception as e:
            return {"file": file, "valid": False, "error": str(e)}

    def validate_all_examples(self, files: Optional[List[Path]] = None) -> Dict:
        """Validate all code examples in markdown files"""
        if files is None:
            files = list(self.project_root.rglob("*.md"))

        all_results = []
        passed = 0
        failed = 0

        for md_file in files:
            if ".git" in str(md_file) or ".pytest_cache" in str(md_file):
                continue

            blocks = self.extract_code_blocks(md_file)
            for block in blocks:
                if block["language"] in ["python", "py"]:
                    result = self.validate_python_example(block["code"], block["file"])
                elif block["language"] in ["bash", "sh"]:
                    result = self.validate_bash_example(block["code"], block["file"])
                else:
                    result = {"file": block["file"], "valid": True, "skipped": f"Language {block['language']} not validated"}

                all_results.append(result)
                if result.get("valid"):
                    passed += 1
                else:
                    failed += 1

        return {
            "results": all_results,
            "total": len(all_results),
            "passed": passed,
            "failed": failed
        }


def cmd_drift(args):
    """Doc/code drift detection command"""
    detector = DriftDetector(Path(args.root))
    openapi_path = Path(args.openapi) if args.openapi else None
    result = detector.run_all_checks(openapi_path)

    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)


def cmd_api_docs(args):
    """API docs generation command"""
    generator = APIDocGenerator(Path(args.root))

    if args.openapi and args.output:
        success = generator.openapi_to_markdown(Path(args.openapi), Path(args.output))
        print(json.dumps({"success": success, "output": args.output}))
        if not success:
            sys.exit(1)
    elif args.fastapi and args.output:
        success = generator.generate_from_fastapi(args.fastapi, Path(args.output))
        print(json.dumps({"success": success, "output": args.output}))
        if not success:
            sys.exit(1)
    else:
        print("Use --openapi <spec> --output <md> or --fastapi <module> --output <json>")


def cmd_diagrams(args):
    """Diagram validation command"""
    validator = DiagramValidator(Path(args.root))
    result = validator.validate_all()
    print(json.dumps(result, indent=2))
    if result["invalid"] > 0 and not args.allow_invalid:
        sys.exit(1)


def cmd_examples(args):
    """Code example validation command"""
    validator = CodeExampleValidator(Path(args.root))

    if args.files:
        md_files = [Path(f) for f in args.files]
    else:
        md_files = None

    result = validator.validate_all_examples(md_files)
    print(json.dumps(result, indent=2))
    if result["failed"] > 0 and not args.allow_failed:
        sys.exit(1)


def cmd_all(args):
    """Run all documentation sync checks"""
    print("=== Documentation Sync (KAN-308 4D) ===\n")

    # 1. Drift detection
    print("1. Doc/Code Drift Detection...")
    detector = DriftDetector(Path(args.root))
    openapi_path = Path(args.openapi) if args.openapi else None
    drift_result = detector.run_all_checks(openapi_path)
    print(f"   Issues found: {drift_result['count']}")
    for issue in drift_result["issues"][:5]:
        print(f"   - {issue['type']}: {issue['message']}")

    # 2. API docs generation
    if args.openapi or args.fastapi:
        print("\n2. API Documentation Generation...")
        generator = APIDocGenerator(Path(args.root))
        if args.openapi and args.output:
            success = generator.openapi_to_markdown(Path(args.openapi), Path(args.output))
            print(f"   Generated: {args.output} ({'OK' if success else 'FAILED'})")
        elif args.fastapi and args.output:
            success = generator.generate_from_fastapi(args.fastapi, Path(args.output))
            print(f"   Generated: {args.output} ({'OK' if success else 'FAILED'})")

    # 3. Diagram validation
    print("\n3. Architecture Diagram Validation...")
    validator = DiagramValidator(Path(args.root))
    diagram_result = validator.validate_all()
    print(f"   Valid: {diagram_result['valid']}, Invalid: {diagram_result['invalid']}")
    for d in diagram_result["diagrams"]:
        if not d["valid"]:
            print(f"   - {d['file']}: {', '.join(d['issues'])}")

    # 4. Code example validation
    print("\n4. Code Example Validation...")
    example_validator = CodeExampleValidator(Path(args.root))
    example_result = example_validator.validate_all_examples()
    print(f"   Passed: {example_result['passed']}, Failed: {example_result['failed']}")
    for r in example_result["results"]:
        if not r.get("valid", True):
            print(f"   - {r['file']}: {r.get('error', 'Unknown error')}")

    print("\n=== Documentation Sync Complete ===")

    # Exit with error if any critical failures
    if drift_result["count"] > 0 and not args.allow_drift:
        sys.exit(1)
    if diagram_result["invalid"] > 0 and not args.allow_invalid:
        sys.exit(1)
    if example_result["failed"] > 0 and not args.allow_failed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Documentation Sync (KAN-308 4D)")
    parser.add_argument("--root", default=".", help="Project root directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Drift detection
    drift_parser = subparsers.add_parser("drift", help="Detect doc/code drift")
    drift_parser.add_argument("--openapi", help="OpenAPI spec path for drift check")
    drift_parser.set_defaults(func=cmd_drift)

    # API docs generation
    api_parser = subparsers.add_parser("api-docs", help="Generate API documentation")
    api_parser.add_argument("--openapi", help="OpenAPI spec file")
    api_parser.add_argument("--fastapi", help="FastAPI module (e.g. main:app)")
    api_parser.add_argument("--output", required=True, help="Output file")
    api_parser.set_defaults(func=cmd_api_docs)

    # Diagram validation
    diag_parser = subparsers.add_parser("diagrams", help="Validate architecture diagrams")
    diag_parser.add_argument("--allow-invalid", action="store_true", help="Don't exit on invalid diagrams")
    diag_parser.set_defaults(func=cmd_diagrams)

    # Code example validation
    ex_parser = subparsers.add_parser("examples", help="Validate code examples in docs")
    ex_parser.add_argument("--files", nargs="*", help="Specific markdown files")
    ex_parser.add_argument("--allow-failed", action="store_true", help="Don't exit on failed examples")
    ex_parser.set_defaults(func=cmd_examples)

    # All-in-one
    all_parser = subparsers.add_parser("all", help="Run all documentation sync checks")
    all_parser.add_argument("--openapi", help="OpenAPI spec for drift/API generation")
    all_parser.add_argument("--fastapi", help="FastAPI module for API generation")
    all_parser.add_argument("--output", help="Output file for API docs")
    all_parser.add_argument("--allow-drift", action="store_true", help="Don't exit on drift")
    all_parser.add_argument("--allow-invalid", action="store_true", help="Don't exit on invalid diagrams")
    all_parser.add_argument("--allow-failed", action="store_true", help="Don't exit on failed examples")
    all_parser.set_defaults(func=cmd_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()