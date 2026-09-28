"""Behavioral checks for the installed mixed Rust/Python wheel."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest


class InstalledWheelContractTests(unittest.TestCase):
    """Verify native identity from outside the repository and source package."""

    def test_package_local_native_import_is_order_independent(self) -> None:
        project_root = os.environ["HORO_PROJECT_ROOT"]
        code = """
import importlib
import json
import os
import sys

sys.path.append(os.environ["HORO_PROJECT_ROOT"])
order = sys.argv[1]
if order == "package-first":
    import rust_core
    fast_math = importlib.import_module("project.core.fast_math")
else:
    fast_math = importlib.import_module("project.core.fast_math")
    import rust_core
print(json.dumps({
    "identity": fast_math.runtime_backend(),
    "origin": rust_core.__native_origin__,
}, sort_keys=True))
"""
        results = []
        for order in ("package-first", "fast-math-first"):
            env = os.environ.copy()
            env["HORO_PROJECT_ROOT"] = project_root
            env.pop("HORO_ALLOW_PYTHON_FALLBACK", None)
            env.pop("PYTHONPATH", None)
            # Private per-invocation CWD instead of the shared world-writable
            # /tmp: `python -c` prepends the CWD to sys.path[0], so a stray
            # inspect.py/json.py there would silently replace the stdlib module
            # and this order-independence assertion would fail for the wrong
            # reason. PYTHONSAFEPATH additionally covers nested interpreters and
            # is a harmless no-op on interpreters older than 3.11.
            if sys.version_info >= (3, 11):
                env["PYTHONSAFEPATH"] = "1"
            else:
                env.pop("PYTHONSAFEPATH", None)
            with tempfile.TemporaryDirectory(prefix="horo-wheel-") as workdir:
                completed = subprocess.run(
                    [sys.executable, "-c", code, order],
                    cwd=workdir,
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            results.append(json.loads(completed.stdout))

        self.assertEqual(results[0], results[1])
        self.assertTrue(results[0]["identity"]["rust_available"])
        self.assertEqual(results[0]["identity"]["rust_version"], "0.1.0")
        self.assertIn("cosine_similarity", results[0]["identity"]["kernels"])
        self.assertIn("site-packages/rust_core/_native", results[0]["origin"])

    def test_standard_wheel_exports_axum_server_entrypoint(self) -> None:
        import rust_core

        self.assertTrue(hasattr(rust_core, "start_rust_axum_server"))
        self.assertIn(
            "start_rust_axum_server",
            rust_core.runtime_backend()["kernels"],
        )


if __name__ == "__main__":
    unittest.main()
