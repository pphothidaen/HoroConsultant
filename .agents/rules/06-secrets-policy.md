# 📜 Rule 06: 2-Tier Priority Secrets Policy & Credentials Governance
> **Scope:** `project/core/config.py`, `scripts/kaggle_notebook_manager.py`, `scripts/cloud_train_orchestrator.py`, `.github/workflows/*`

## 📌 Priority Tier Architecture

All agents and modules MUST adhere strictly to the **2-Tier Priority Secrets Policy**:

```
                       ┌─────────────────────────────────────────┐
                       │    1st Priority: DOPPLER SECRETS STORE  │
                       │      (Centralized Cloud Secrets Vault)  │
                       └────────────────────┬────────────────────┘
                                            │
                                  (If missed in Doppler)
                                            │
                                            ▼
                        [WARNING] Secret 'KEY' not found in Doppler.
                      Falling back to 2nd Priority Secrets Store...
                                            │
                                            ▼
                       ┌────────────────────┴────────────────────┐
                       │   2nd Priority: PLATFORM SECRETS STORE  │
                       │  (Kaggle Secrets Client / GitHub / .env)│
                       └─────────────────────────────────────────┘
```

## 🛡️ Core Rules & Warnings
1. **1st Priority (DOPPLER SECRETS STORE)**:
   - Always check `DOPPLER_TOKEN` or Doppler environment variables first.
2. **Warning on Doppler Miss**:
   - If a secret is NOT found in Doppler, log an explicit warning:
     `[WARNING] Secret '{key}' not found in 1st Priority (DOPPLER). Falling back to 2nd Priority ({platform_name})...`
3. **2nd Priority (PLATFORM SECRETS STORE)**:
   - **Kaggle**: Use `from kaggle_secrets import UserSecretsClient` to load all 7 keys:
     `['APP_SUPABASE_KEY', 'APP_SUPABASE_URL', 'DOPPLER_TOKEN', 'GH_TOKEN', 'HF_TOKEN', 'KAGGLE_TOKEN', 'WANDB_KEY']`
   - **GitHub Actions**: Pass secrets via `secrets.*` in `.github/workflows/kaggle_finetune.yml`.
   - **Local Development**: Read from `.env` or system environment variables.
