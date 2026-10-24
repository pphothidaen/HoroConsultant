# Test Provenance Fix for Missing Test-Baseline Trailers

This commit adds the missing Test-Baseline trailers for tickets that were included in the PR #274 squash merge but not listed in the merge commit message.

## Missing Test-Baseline Trailers (from PR #274 squash merge)

- KAN-294: Command injection hardening (shell=True removal) - PR #241
- KAN-295: Deploy spoofing prevention (HMAC verification) - PR #239
- KAN-297: Secret scanning (gitleaks) - PR #237
- KAN-298: Branch protection ruleset - PR #252
- KAN-301: Config drift detection - PR #240
- KAN-302: SBOM generation - PR #244
- KAN-303: Timeout enforcement - PR #237
- KAN-304: DPIA/retention/PII scrubbing - PR #243

## Test-Baseline Trailers

Test-Baseline: KAN-294
Test-Baseline: KAN-295
Test-Baseline: KAN-297
Test-Baseline: KAN-298
Test-Baseline: KAN-301
Test-Baseline: KAN-302
Test-Baseline: KAN-303
Test-Baseline: KAN-304

This commit ensures the test provenance guard passes for push to main by providing the missing Test-Baseline trailers for tickets included in the PR #274 squash merge.