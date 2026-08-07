# 📜 Rule 01: Coding Standards & Logging Guidelines
> **Scope:** `project/**/*.py`, `scripts/**/*.py`, `tests/**/*.py`

## 📌 Requirements
1. **Python 3.12 Compatibility**: Use modern Python 3.12 type annotations (`list[str]`, `dict[str, Any]`, `X | None`).
2. **Pure ASCII Logging Guard**:
   - All `logger` outputs and stdout must use Pure ASCII bracketed tags (`[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]`, `[START]`, `[MODEL]`, `[CUDA]`, `[AUDIT]`).
   - Do NOT use Unicode Emojis inside subprocess or ipykernel logs to prevent `UnicodeEncodeError` surrogate crashes on Tornado/Jupyter.
3. **Environment Setup**:
   ```python
   os.environ["PYTHONIOENCODING"] = "utf-8"
   os.environ["PYTHONUTF8"] = "1"
   os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
   os.environ["TRANSFORMERS_VERBOSITY"] = "error"
   ```
4. **Preserve Comments & Docstrings**: Maintain existing inline comments, NOAA Spencer formulas, and docstrings unless explicitly asked to modify.
