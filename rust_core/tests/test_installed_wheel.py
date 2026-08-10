"""Behavioral checks for the installed mixed Rust/Python wheel."""

from __future__ import annotations

import json
import os
import subprocess
import sys
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
            completed = subprocess.run(
                [sys.executable, "-c", code, order],
                cwd="/tmp",
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


if __name__ == "__main__":
    unittest.main()
