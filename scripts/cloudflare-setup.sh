#!/bin/bash
set -euo pipefail

cd /Users/kimlenglim/Project/HoroConsultant

# Read token
TOKEN=$(grep '^CLOUDFLARE_API_TOKEN=' .env | cut -d'"' -f2)
ACCOUNT_ID="bda49e4e77e00609cb1ef68561b0d9eb"

echo "Token: ${TOKEN:0:10}..."

# Verify token
echo "--- Verify token ---"
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Create KV namespace
echo "--- Create KV namespace ---"
KV_RESULT=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/storage/kv/namespaces" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"horoconsultant-cache"}')
echo "$KV_RESULT" | python3 -m json.tool

# Extract KV ID (or look up existing if already created)
KV_ID=$(echo "$KV_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('id',''))" 2>/dev/null || true)
if [ -z "$KV_ID" ]; then
  echo "Checking for existing KV namespace 'horoconsultant-cache'..."
  KV_LIST=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/storage/kv/namespaces" \
    -H "Authorization: Bearer $TOKEN")
  KV_ID=$(echo "$KV_LIST" | python3 -c "import sys,json
for ns in json.load(sys.stdin).get('result',[]):
    if ns.get('title') == 'horoconsultant-cache' or ns.get('label') == 'horoconsultant-cache':
        print(ns.get('id',''))
        break" 2>/dev/null || true)
fi

echo "KV Namespace ID: $KV_ID"

if [ -n "$KV_ID" ]; then
  python3 -c "
import re
with open('wrangler.toml', 'r') as f:
    c = f.read()
new_c = re.sub(r'(\[\[kv_namespaces\]\][\s\S]*?id\s*=\s*\")[^\"]+(\")', r'\g<1>${KV_ID}\g<2>', c)
with open('wrangler.toml', 'w') as f:
    f.write(new_c)
print('[OK] Updated wrangler.toml with KV namespace ID: ${KV_ID}')
"
fi

# Create R2 bucket
echo "--- Create R2 bucket ---"
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"horoconsultant-artifacts"}' | python3 -m json.tool || true

echo "Done! Cloudflare resources are configured."

