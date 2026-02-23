#!/usr/bin/env python3
"""
Create test agenda items with special characters
"""

import json
import urllib.request
import urllib.parse
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration
# =============================================================================

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Create Test Agenda Items")
print("=" * 70)

token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
data = urllib.parse.urlencode({
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'scope': f'{ORG_URL}/.default'
}).encode('utf-8')

req = urllib.request.Request(token_url, data=data)
with urllib.request.urlopen(req) as resp:
    TOKEN = json.loads(resp.read().decode('utf-8'))['access_token']

print("\n✓ Authentication successful")

# =============================================================================
# Get first meeting ID
# =============================================================================

print("\n✓ Fetching test meetings...")

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

meetings_url = f"{API_URL}/crad9_meetings?$select=crad9_meetingid,crad9_newcolumn&$top=1"
req = urllib.request.Request(urllib.parse.quote(meetings_url, safe=':/?=&$,'), headers=headers)

with urllib.request.urlopen(req) as resp:
    meetings = json.loads(resp.read().decode('utf-8'))

if not meetings.get('value'):
    print("\n✗ No test meetings found. Run setup_test_meetings.py first.")
    sys.exit(1)

meeting = meetings['value'][0]
meeting_id = meeting['crad9_meetingid']
meeting_name = meeting['crad9_newcolumn']

print(f"  Meeting: {meeting_name}")
print(f"  ID: {meeting_id}")

# =============================================================================
# Create test agenda items with special characters
# =============================================================================

print("\n" + "=" * 70)
print("Creating Test Agenda Items (Special Characters)")
print("=" * 70)

test_agenda_items = [
    {
        "name": "Item #1: Budget Review & Approval",
        "sequence": 1,
        "description": "Review Q1 budget allocations"
    },
    {
        "name": "Item #2: New Hire? (Y/N)",
        "sequence": 2,
        "description": "Discuss hiring needs for Q2/Q3"
    },
    {
        "name": "Item #3: Tech Stack: Python/Node.js",
        "sequence": 3,
        "description": "Technology decisions for upcoming projects"
    },
    {
        "name": "Item #4: Client\\Server Architecture",
        "sequence": 4,
        "description": "Review client-server architecture design"
    },
    {
        "name": "Item #5: [URGENT] Security Review",
        "sequence": 5,
        "description": "Urgent security issues to address"
    }
]

for agenda in test_agenda_items:
    print(f"\n✓ Creating: {agenda['name']}...")

    agenda_payload = {
        "crad9_name": agenda['name'],
        "crad9_sequence": agenda['sequence'],
        "crad9_description": agenda['description'],
        "crad9_meeting@odata.bind": f"/crad9_meetings({meeting_id})",
        "crad9_foldercreated": False
    }

    headers['Content-Type'] = 'application/json'
    create_url = f"{API_URL}/crad9_agendaitems"
    req_data = json.dumps(agenda_payload).encode('utf-8')
    req = urllib.request.Request(create_url, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"  ✓ Created: {result.get('crad9_agendaitemid')}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"  ✗ Error (HTTP {e.code}):")
        try:
            err_json = json.loads(err_body)
            print(f"    {err_json.get('error', {}).get('message', err_body[:200])}")
        except:
            print(f"    {err_body[:200]}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  ✓ Agenda Items Created")
print("=" * 70)
print()
print(f"  Meeting: {meeting_name}")
print(f"  Agenda Items: {len(test_agenda_items)}")
print()
print("  Expected Agenda Item Folder Names (sanitized):")
print("    • Item #1- Budget Review & Approval")
print("    • Item #2- New Hire (Y-N)")
print("    • Item #3- Tech Stack- Python-Node.js")
print("    • Item #4- Client-Server Architecture")
print("    • Item #5- [URGENT] Security Review")
print()
print("  The Power Automate workflows should now:")
print("    1. Create meeting folder in SharePoint")
print("    2. Create subfolders for each agenda item")
print("    3. Populate crad9_folderurl and crad9_spfolderurl fields")
print()
