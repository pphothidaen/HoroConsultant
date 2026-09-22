#!/usr/bin/env bash
# ============================================================
# sync-render-secrets.sh — Doppler (prd) → Render env vars sync
# ============================================================
# Upserts every Doppler prd secret into the Render web service,
# excluding gateway-only credentials that the backend never needs.
#
# Required environment:
#   DOPPLER_SERVICE_TOKEN  Doppler service token (dp.st.prd.*)
#   RENDER_API_KEY         Render API token (rnd_...)
#   RENDER_SERVICE_ID      Render service id (srv-...)
#
# Usage:
#   DOPPLER_SERVICE_TOKEN=... RENDER_API_KEY=... RENDER_SERVICE_ID=... \
#     ./scripts/sync-render-secrets.sh
#
# Optional environment:
#   DOPPLER_PROJECT   (default: horo-consultant)
#   DOPPLER_CONFIG    (default: prd)
# ============================================================
set -euo pipefail

: "${DOPPLER_SERVICE_TOKEN:?DOPPLER_SERVICE_TOKEN is required}"
: "${RENDER_API_KEY:?RENDER_API_KEY is required}"
: "${RENDER_SERVICE_ID:?RENDER_SERVICE_ID is required}"

DOPPLER_PROJECT="${DOPPLER_PROJECT:-horo-consultant}"
DOPPLER_CONFIG="${DOPPLER_CONFIG:-prd}"

# Gateway-only credentials and Render/Doppler self-references are never pushed.
EXCLUDE_PREFIXES=(VERCEL_ GITHUB_ HF_STATIC_)
EXCLUDE_KEYS=(DOPPLER_SERVICE_TOKEN DOPPLER_TOKEN RENDER_API_KEY RENDER_SERVICE_ID RENDER_TOKEN)

excluded() {
  local key="$1"
  for prefix in "${EXCLUDE_PREFIXES[@]}"; do
    [[ "${key}" == "${prefix}"* ]] && return 0
  done
  for key_name in "${EXCLUDE_KEYS[@]}"; do
    [[ "${key}" == "${key_name}" ]] && return 0
  done
  return 1
}

echo "Fetching secrets from Doppler ${DOPPLER_PROJECT}/${DOPPLER_CONFIG}..."
pairs=$(python3 - "$DOPPLER_SERVICE_TOKEN" "$DOPPLER_PROJECT" "$DOPPLER_CONFIG" <<'PYEOF'
import json, sys, urllib.request

token, project, config = sys.argv[1], sys.argv[2], sys.argv[3]
url = (f"https://api.doppler.com/v3/configs/config/secrets"
       f"?project={project}&config={config}&include_values=true")
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
secrets = json.load(urllib.request.urlopen(req))["secrets"]

EXCLUDE_PREFIXES = ("VERCEL_", "GITHUB_", "HF_STATIC_")
EXCLUDE_KEYS = {"DOPPLER_SERVICE_TOKEN", "DOPPLER_TOKEN", "RENDER_API_KEY",
                "RENDER_SERVICE_ID", "RENDER_TOKEN"}

env_vars = []
for key, wrapper in sorted(secrets.items()):
    value = (wrapper.get("computed") if isinstance(wrapper, dict) else wrapper) or ""
    if any(key.startswith(p) for p in EXCLUDE_PREFIXES) or key in EXCLUDE_KEYS:
        continue
    env_vars.append({"key": key, "value": value})
print(json.dumps(env_vars))
PYEOF
)

count=$(printf '%s' "$pairs" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
echo "Upserting ${count} env vars into Render service ${RENDER_SERVICE_ID}..."

printf '%s' "$pairs" | curl -sS -X PATCH \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @- \
  "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/env-vars" > /dev/null

echo "Sync complete. Render will redeploy with the new environment."
