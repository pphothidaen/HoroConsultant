"""
rust_core Python Package Initialiser
Re-exports Rust extension functions compiled via PyO3.
"""

try:
    from .rust_core import *
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
