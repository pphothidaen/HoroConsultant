"""
rust_core Python Package Initialiser
Dynamically loads and re-exports Rust PyO3 native extension functions.
"""

import sys
import importlib.util
from pathlib import Path

RUST_AVAILABLE = False

for p in sys.path:
    p_path = Path(p)
    if p_path.exists():
        candidates = list(p_path.rglob("*rust_core*.so")) + list(p_path.rglob("*rust_core*.dylib"))
        for so in candidates:
            try:
                spec = importlib.util.spec_from_file_location("rust_core_native", str(so))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    for k in dir(mod):
                        if not k.startswith("_"):
                            globals()[k] = getattr(mod, k)
                    RUST_AVAILABLE = True
                    break
            except Exception:
                pass
        if RUST_AVAILABLE:
            break
