#!/usr/bin/env python3
"""Investigate Sprint F tickets and link them to the release version."""
import os, json, sys, time, urllib.request, urllib.error, urllib.parse
from base64 import b64encode

BASE = os.environ['JIRA_BASE_URL']
EMAIL = os.environ['JIRA_EMAIL']
TOKEN = os.environ['JIRA_API_TOKEN']

def api_get(path):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url)
    auth = b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, body

def api_post(path, data):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method='POST')
    auth = b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read()) if resp.read else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, body

def api_put(path, data):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, method='PUT')
    auth = b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, {}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, body

def api_request_retry(method, path, data=None, max_retries=4):
    """Retry pattern for rate limits (429) and server busy (503)."""
    for attempt in range(max_retries):
        if method == 'GET':
            status, body = api_get(path)
        elif method == 'POST':
            status, body = api_post(path, data)
        elif method == 'PUT':
            status, body = api_put(path, data)
        else:
            raise ValueError(f"Unknown method {method}")
        
        if status == 429:
            wait = 25
            print(f"  Rate limited (429), waiting {wait}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
            continue
        elif status == 503:
            wait = 15
            print(f"  Server busy (503), waiting {wait}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
            continue
        return status, body
    return 429, {"error": "max retries exceeded"}

# Try to fetch a specific issue to see structure
print("=" * 60)
print("Fetching specific issue KAN-38")
print("=" * 60)
status, result = api_request_retry('GET', "/rest/api/3/issue/KAN-38?fields=summary,labels,fixVersions,status")
print(f"Status: {status}")
print(json.dumps(result, indent=2)[:2000])

# Try the search with fields parameter
print()
print("=" * 60)
print("Search with fields parameter")
print("=" * 60)
search_data = {
    "jql": "project=KAN",
    "maxResults": 5,
    "fields": ["summary", "labels", "fixVersions", "status"]
}
status, result = api_request_retry('POST', "/rest/api/3/search/jql", search_data)
print(f"Status: {status}")
print(json.dumps(result, indent=2)[:2000])
