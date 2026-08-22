# Local Release Readiness Evidence (2026-08-17)

- `python3 scripts/sync_sdlc_agents.py --check` → passed
- `python3 scripts/sync_codex_agents.py --check` → passed
- `python3 project/core/code_reviewer.py --scan-secrets` → passed (1,493 files)
- `python3 project/core/code_reviewer.py --review --use-python` → READY_FOR_PROD (`605 passed`, `8 skipped`, `12 warnings`)
- `python3 project/core/code_reviewer.py --review` → READY_FOR_PROD (`605 passed`, `8 skipped`, `12 warnings`)
- `python3 -m pytest -q project/tests/` → `566 passed`, `8 skipped`, `12 warnings`
- `python3 -m pytest project/tests/test_ai_provider_router.py project/tests/test_ai_provider_router_tier3.py project/tests/test_llm_multirouter.py` → `19 passed`
- `python3 -m pytest project/tests/test_observability.py project/tests/test_rust_extensions.py` → `25 passed`
- `python3 scripts/grafana_cloud_exporter.py --check-connection --dry-run` → completed with local fallback, cloud URL unreachable from this environment
- `cd rust_core && cargo test --no-default-features --test test_vector_search` → `2 passed`
- `python3 scripts/run_quality_gate.py` → READY_FOR_PRODUCTION (`100% PASSED`)
- `python3 scripts/run_button_regression.py` → `25/25 PASSED` (`project/tests/button_regression_report.json`)
- `HF_BACKEND_URL=https://core-backend.hf.space HF_STATIC_CDN_URL=https://static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` → `0/3` (legacy target check)
- `.env` now defines `HF_BACKEND_SPACE_ID`, `HF_BACKEND_URL`, and `HF_STATIC_CDN_URL` for bootstrap, but canonical HF probe remains blocked by workspace DNS (`0/3` in this runtime).
- `HF_BACKEND_URL=https://core-backend.hf.space HF_STATIC_CDN_URL=https://static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` → `0/3` (legacy target check)
- `python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check.json` (Vercel-target verification) → `2/3` (`static` `404`, `/health` `200`, `/api/v1/interpret` `200`)
- `HF_BACKEND_URL=https://pphothidaen-horoconsultant-core-backend.hf.space HF_STATIC_CDN_URL=https://pphothidaen-horoconsultant-core-backend.static.hf.space python3 scripts/run_live_health_verification.py --json-output project/tests/backend-release-check-hf-canonical.json` → `0/3` (canonical HF probe) in this runtime.
- `python3 -m pytest -q project/tests/test_post_train_fuse.py project/tests/test_api_router_external.py project/tests/test_ingest_vault.py project/tests/test_swiss_ephemeris.py` → `19 passed`
- `python3 -m pytest project/tests/test_web_regression.py -q` → `11 passed, 4 skipped`
- `python3 scripts/run_vercel_prod_curl_regression.py --url https://horo-consultant-psi.vercel.app --use-python` → `2/3` (`GET /health`/OPTIONS pass; `POST /api/v1/bazi/interpret` `503` + missing `X-AI-Source`/`X-AI-Model`)
- `HORO_PUBLIC_URL=https://horo-consultant-psi.vercel.app python3 scripts/run_prod_e2e_playwright.py --profile smoke` → reached target and presets, then failed on canonical API fallback (`503`) plus UI waits (`#location_search` fill timeout; interpretation-tab click timeout on script abort).
- `HF_BACKEND_SPACE_ID="pphothidaen/horoconsultant-core-backend" HF_TOKEN="[REDACTED]" python3 scripts/publish_space_hf.py --space-id "$HF_BACKEND_SPACE_ID" --sdk docker` → failed immediately (`HF Token authentication failed: [Errno 8] nodename nor servname provided, or not known`) because DNS to `huggingface.co` is unavailable in this runtime.
- `python3 - <<'PY'` socket resolution probe (`huggingface.co`, `pphothidaen-horoconsultant-core-backend.hf.space`, `api.huggingface.co`) → all three hosts unresolved in this runtime (`Errno 8`, `nodename nor servname provided, or not known`).

- `python3 - <<"PY"` DNS probe on key external hosts was previously used for historical context; authoritative evidence for this run remains the socket/DNS resolver probe above, which reports unresolved hosts in this runtime.

- `python3 scripts/run_quality_gate.py` → `READY` (`100% PASSED`, 4/4 stages).
- `scutil --dns` output and `/etc/resolv.conf` may not match request-level behavior; direct probe output and API checks are now the authoritative source for this pass.
