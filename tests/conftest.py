import os

# Enable explicit Python fallback by default in local pytest test runner if not overridden
os.environ.setdefault("HORO_ALLOW_PYTHON_FALLBACK", "1")
