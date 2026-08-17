# 📜 Rule 04: MLOps & Kaggle Fine-Tuning Standards
> **Scope:** `scripts/kaggle_notebook_manager.py`, `scripts/cloud_train_orchestrator.py`, `project/kaggle_kernel/*`

## 📌 Requirements
1. **Locked Stack**:
   - `transformers == 4.44.2`
   - `peft == 0.12.0`
   - `trl == 0.11.0`
   - `accelerate >= 0.34.0, < 1.0.0`
   - `bitsandbytes == 0.43.3`
   - `datasets >= 2.21.0`
   - `huggingface_hub == 0.25.1`
2. **Kaggle PyTorch Integrity**:
   - NEVER run `pip install torch==...` to reinstall PyTorch in Kaggle environment (causes `libcudnn.so.8` missing crash).
3. **Pre-Flight CUDA Audit & CPU Fallback**:
   - `cloud_train_orchestrator.py` must execute instant CUDA arithmetic test (`t32 + t32`).
   - If CUDA kernel test fails (e.g. `sm_60` P100 unsupported GPU), automatically fallback to CPU execution mode (`use_cuda = False`) to guarantee 100% completion (Exit Code 0).
