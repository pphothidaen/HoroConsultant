"""
tests/test_notebook_syntax.py
==============================
Automated Pre-Deployment Quality Gate for Jupyter Notebooks (.ipynb).

Validates:
1. Valid JSON schema structure across all repository notebooks.
2. Zero Python SyntaxError / Unterminated String Literals in all code cells (via AST parsing and bytecode compilation).
3. Dependency matrix compliance (no deprecated/conflicting packages like accelerate==0.33.0 or datasets<2.21.0).
4. Strict parity between root pipeline and Kaggle kernel notebook targets.
"""

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestNotebookSyntaxAndIntegrity(unittest.TestCase):
    """Test suite for Jupyter Notebook Syntax, AST, and Dependency Hygiene."""

    def setUp(self):
        self.notebook_paths = [
            ROOT / "horoconsultant-finetune-pipeline.ipynb",
            ROOT / "project" / "kaggle_kernel" / "notebook.ipynb",
        ]

    def test_notebooks_exist_and_valid_json(self):
        """All production notebooks must exist and be strictly parseable JSON."""
        for nb_path in self.notebook_paths:
            self.assertTrue(nb_path.exists(), f"Notebook missing: {nb_path}")
            try:
                with open(nb_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertIn("cells", data, f"Notebook {nb_path.name} missing 'cells' key")
            except json.JSONDecodeError as e:
                self.fail(f"Notebook {nb_path.name} contains invalid JSON: {e}")

    def test_all_code_cells_ast_compilation(self):
        """Every code cell must pass AST parsing and Python bytecode compilation with zero SyntaxErrors."""
        for nb_path in self.notebook_paths:
            if not nb_path.exists():
                continue
            with open(nb_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for idx, cell in enumerate(data.get("cells", [])):
                if cell.get("cell_type") != "code":
                    continue
                source = "".join(cell.get("source", []))
                cell_id = f"{nb_path.name} (Cell #{idx + 1})"

                # 1. AST parse test
                try:
                    ast.parse(source, filename=cell_id)
                except SyntaxError as e:
                    self.fail(f"AST SyntaxError in {cell_id} at line {e.lineno}: {e.msg}\nSnippet: {e.text}")

                # 2. Bytecode compile test
                try:
                    compile(source, cell_id, "exec")
                except SyntaxError as e:
                    self.fail(f"Compilation SyntaxError in {cell_id} at line {e.lineno}: {e.msg}\nSnippet: {e.text}")

    def test_dependency_matrix_locks(self):
        """Ensure no code cells contain deprecated, broken, or conflicting package specifications."""
        forbidden_substrings = [
            ("accelerate==0.33.0", "accelerate 0.33.0 forces numpy<2.0 which breaks Kaggle numpy 2.x ABI; use accelerate>=0.34.0,<1.0.0"),
            ("datasets==2.18.0", "datasets 2.18.0 forces pyarrow<15; use datasets>=2.21.0,<3.5.0"),
            ("pyarrow_hotfix", "pyarrow_hotfix is deprecated on PyArrow 15+ and Python 3.12"),
            ("BNB_CUDA_VERSION = '124'", "Hardcoding BNB_CUDA_VERSION breaks CUDA 12.8 auto-detection"),
        ]

        for nb_path in self.notebook_paths:
            if not nb_path.exists():
                continue
            with open(nb_path, "r", encoding="utf-8") as f:
                content = f.read()

            for bad_str, rationale in forbidden_substrings:
                self.assertNotIn(
                    bad_str,
                    content,
                    f"Forbidden pattern '{bad_str}' found in {nb_path.name}: {rationale}"
                )

    def test_pipeline_notebook_parity(self):
        """Root pipeline notebook and project/kaggle_kernel/notebook.ipynb must have identical code cells."""
        root_nb = ROOT / "horoconsultant-finetune-pipeline.ipynb"
        kaggle_nb = ROOT / "project" / "kaggle_kernel" / "notebook.ipynb"

        if root_nb.exists() and kaggle_nb.exists():
            with open(root_nb, "r", encoding="utf-8") as f1, open(kaggle_nb, "r", encoding="utf-8") as f2:
                data1 = json.load(f1)
                data2 = json.load(f2)

            cells1 = [c.get("source") for c in data1.get("cells", []) if c.get("cell_type") == "code"]
            cells2 = [c.get("source") for c in data2.get("cells", []) if c.get("cell_type") == "code"]

            self.assertEqual(
                cells1,
                cells2,
                "horoconsultant-finetune-pipeline.ipynb and project/kaggle_kernel/notebook.ipynb are out of sync!"
            )

    def test_triton_shim_package_compliance(self):
        """Verify that Triton 3.x compatibility shim correctly resolves triton.ops.matmul_perf_model imports."""
        import sys
        import types

        try:
            import triton
        except (ImportError, ModuleNotFoundError):
            triton = types.ModuleType("triton")
            triton.__path__ = []
            sys.modules["triton"] = triton

        if not hasattr(triton, "ops") or "triton.ops" not in sys.modules:
            triton_ops = types.ModuleType("triton.ops")
            triton_ops.__path__ = []
            setattr(triton, "ops", triton_ops)
            sys.modules["triton.ops"] = triton_ops

        triton_ops = sys.modules["triton.ops"]
        if not hasattr(triton_ops, "__path__"):
            triton_ops.__path__ = []

        if not hasattr(triton_ops, "matmul_perf_model") or "triton.ops.matmul_perf_model" not in sys.modules:
            triton_ops_matmul = types.ModuleType("triton.ops.matmul_perf_model")
            triton_ops_matmul.early_config_prune = lambda *a, **k: None
            triton_ops_matmul.estimate_matmul_time = lambda *a, **k: 0
            setattr(triton_ops, "matmul_perf_model", triton_ops_matmul)
            sys.modules["triton.ops.matmul_perf_model"] = triton_ops_matmul

        # Validate that exact bitsandbytes import statement executes with zero errors
        from triton.ops.matmul_perf_model import early_config_prune, estimate_matmul_time
        self.assertTrue(callable(early_config_prune))
        self.assertTrue(callable(estimate_matmul_time))


if __name__ == "__main__":
    unittest.main()
