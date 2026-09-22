#!/usr/bin/env python3
"""Create Sprint F Bridge Production version and link Sprint F tickets."""
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

# Step 1: Verify version exists
print("=" * 60)
print("Step 1: Verify version exists")
print("=" * 60)
target_version_id = "10001"  # Already exists from previous run
status, versions = api_request_retry('GET', "/rest/api/3/project/KAN/versions")
if isinstance(versions, list):
    for v in versions:
        if v['name'] == 'Sprint F Bridge Production' and not v.get('archived'):
            target_version_id = v['id']
            print(f"Version found: ID={target_version_id}, Name={v['name']}")
            break
    else:
        print("Version not found!")
        target_version_id = None
else:
    print("Error:", versions)
    target_version_id = None

if not target_version_id:
    print("ERROR: Version not found")
    sys.exit(1)

# Step 2: Find all KAN tickets and check their fixVersions
print()
print("=" * 60)
print("Step 2: Find all KAN tickets")
print("=" * 60)

# Use pagination to get all issues
all_issues = []
next_page_token = None
while True:
    search_data = {
        "jql": "project=KAN",
        "maxResults": 50,
        "fields": ["summary", "fixVersions", "labels"]
    }
    if next_page_token:
        search_data["nextPageToken"] = next_page_token
    
    status, result = api_request_retry('POST', "/rest/api/3/search/jql", search_data)
    if 'error' not in result and 'errorMessages' not in result:
        issues = result.get('issues', [])
        all_issues.extend(issues)
        print(f"  Fetched {len(issues)} issues (total so far: {len(all_issues)})")
        
        if result.get('isLast', True):
            break
        next_page_token = result.get('nextPageToken')
        if not next_page_token:
            break
    else:
        print("Error:", result)
        break

print(f"\nTotal KAN issues: {len(all_issues)}")

# Categorize tickets
already_linked = []
to_link = []
for issue in all_issues:
    fix_versions = issue['fields'].get('fixVersions', [])
    version_ids = [v['id'] for v in fix_versions]
    if target_version_id in version_ids:
        already_linked.append(issue['key'])
    else:
        to_link.append(issue['key'])

print(f"\nAlready linked to Sprint F Bridge Production: {len(already_linked)}")
for k in already_linked:
    print(f"  {k}")
print(f"\nNeed to be linked: {len(to_link)}")
for k in to_link:
    print(f"  {k}")

# Step 3: Link tickets
print()
print("=" * 60)
print("Step 3: Link tickets to version")
print("=" * 60)

if not to_link:
    print("No tickets to link")
else:
    linked = []
    failed = []
    for key in to_link:
        print(f"  Linking {key}...")
        update_data = {
            "fields": {
                "fixVersions": [{"id": target_version_id}]
            }
        }
        status, result = api_request_retry('PUT', f"/rest/api/3/issue/{key}", update_data)
        if status in (200, 204):
            linked.append(key)
            print(f"    SUCCESS")
        else:
            failed.append(key)
            print(f"    FAILED: status={status}, result={result}")
        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Release Version: Sprint F Bridge Production")
    print(f"Version ID: {target_version_id}")
    print(f"Already Linked ({len(already_linked)}):")
    for k in already_linked:
        print(f"  - {k}")
    print(f"Newly Linked ({len(linked)}):")
    for k in linked:
        print(f"  - {k}")
    if failed:
        print(f"Failed Tickets ({len(failed)}):")
        for k in failed:
            print(f"  - {k}")
