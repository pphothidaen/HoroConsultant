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
  -d '{"label":"horoconsultant-cache"}')
echo "$KV_RESULT" | python3 -m json.tool

# Extract KV ID
KV_ID=$(echo "$KV_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('id',''))" 2>/dev/null)
echo "KV Namespace ID: $KV_ID"

# Create R2 bucket
echo "--- Create R2 bucket ---"
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/r2/buckets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"horoconsultant-artifacts"}' | python3 -m json.tool

echo "Done!"
