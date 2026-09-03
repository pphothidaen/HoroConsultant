# scripts - Scoped Agent Instructions

## Scope & Precedence
- Governs automation scripts, CI/CD utilities, and ecosystem sync tools in `scripts/`.
- Root Universal Safeguards Precedence: Root `AGENTS.md`, `.agents/rules/`, and repository safety mandates strictly supersede this document.
- Portability: Ensure scripts run cross-platform on macOS and Linux runners without platform-specific assumptions.

## DevOps Deployment Hygiene
- Ensure all automation scripts are idempotent, robust, and safe to execute in CI and local environments.
- Verify environment prerequisites before triggering mutations; clean up temporary resources on exit.
- Keep execution dependencies self-contained and standard-library-first where possible.
- Avoid side-effects during import; wrap entrypoints under `if __name__ == "__main__":`.
- Use explicit subprocess timeouts and avoid unhandled hanging background processes.

## Pure ASCII Logging
- Enforce strict ASCII-only output in all script stdout/stderr logging.
- Do not emit raw emojis, decorative Unicode glyphs, or non-ASCII characters that break CI terminals.
- Format console reports with clear status tags like `[OK]`, `[ERROR]`, `[WARN]`, or `[INFO]`.
- Keep telemetry log records clean, parseable, and structured for automated pipelines.
- Sanitize external string payloads before printing to maintain ASCII compliance.

## Two-Tier Secrets & Security
- Strictly observe 2-tier secret architecture: Doppler / Vault credentials separated from application envs.
- Never hardcode secrets, API keys, session tokens, or private credentials in scripts or logs.
- Scrub sensitive values and credential tokens from command outputs and error traces.
- Enforce restricted file permissions on temporary configuration and credential files.

## Fail-Closed Release Verification
- All build, synchronization, and deployment gates must fail closed on any validation error.
- Verify ecosystem alignment with `python3 scripts/sync_ai_agent_ecosystem.py --check` prior to release claims.
- Never bypass broken quality checks or proceed on partial failures.
- Halt deployment immediately when pre-flight health checks fail.
