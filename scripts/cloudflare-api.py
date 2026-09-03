#!/usr/bin/env python3
"""Cloudflare KV + R2 setup using requests library."""
import json
import os
import sys

# Try to import requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False
    print("WARNING: requests library not found, using urllib")

# Read token from .env
token = None
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('CLOUDFLARE_API_TOKEN='):
            token = line.split('=', 1)[1].strip('"').strip("'")
            break

if not token:
    print("ERROR: CLOUDFLARE_API_TOKEN not found in .env")
    sys.exit(1)

ACCOUNT_ID = "bda49e4e77e00609cb1ef68561b0d9eb"
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"Token: {token[:10]}... (length: {len(token)})")
print(f"Using: {'requests' if HAS_REQUESTS else 'urllib'}")

# Verify token
print("\n--- Verify token ---")
if HAS_REQUESTS:
    resp = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=headers, timeout=10)
    data = resp.json()
    print(f"Status: {resp.status_code}")
    print(f"Result: {data.get('success')} — {data.get('messages', [{}])[0].get('message', '')}")
else:
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        print(f"Result: {data.get('success')} — {data.get('messages', [{}])[0].get('message', '')}")

if not data.get('success'):
    print("Token verification failed!")
    sys.exit(1)

# Create KV namespace
print("\n--- Create KV namespace ---")
kv_data = {"label": "horoconsultant-cache"}
if HAS_REQUESTS:
    resp = requests.post(f"{BASE_URL}/storage/kv/namespaces", headers=headers, json=kv_data, timeout=10)
    data = resp.json()
    print(f"Status: {resp.status_code}")
else:
    req = urllib.request.Request(f"{BASE_URL}/storage/kv/namespaces", data=json.dumps(kv_data).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

if data.get('success'):
    print(f"KV Namespace ID: {data['result']['id']}")
    print(f"KV Namespace Label: {data['result']['label']}")
else:
    print(f"KV Error: {data.get('errors')}")

# Create R2 bucket
print("\n--- Create R2 bucket ---")
r2_data = {"name": "horoconsultant-artifacts"}
if HAS_REQUESTS:
    resp = requests.post(f"{BASE_URL}/r2/buckets", headers=headers, json=r2_data, timeout=10)
    data = resp.json()
    print(f"Status: {resp.status_code}")
else:
    req = urllib.request.Request(f"{BASE_URL}/r2/buckets", data=json.dumps(r2_data).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

if data.get('success'):
    print(f"R2 Bucket: {data['result']['name']}")
else:
    print(f"R2 Error: {data.get('errors')}")

print("\nDone!")
