# scripts/ — Automation & Cloud Fine-Tuning Scripts

## Purpose
Automation scripts for deployment, fine-tuning, testing, and CI/CD.

## Key Files
- `scripts/publish_space_hf.py` — Publish Docker backend to HF Spaces
- `scripts/auto_deploy_all.sh` — Local release readiness dry-run
- `scripts/run_button_regression.py` — UI endpoint contract regression
- `scripts/run_prod_version_e2e.py` — Production version E2E regression
- `scripts/run_live_health_verification.py` — Live health check
- `scripts/synthetic_health_monitor.py` — Synthetic monitoring
- `scripts/sync_ai_agent_ecosystem.py` — Multi-platform agent sync
- `scripts/test_provenance_guard.py` — Test-first Git provenance

## Environment Variables
- `HF_TOKEN` / `HUGGINGFACE_TOKEN` — HF deployment token
- `VERCEL_TOKEN` — Vercel admin (optional)
- `DOPPLER_TOKEN` — Doppler secret management
