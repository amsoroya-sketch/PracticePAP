#!/usr/bin/env python3
"""
Create test agenda items with special characters - FIXED VERSION

Uses correct navigation property name based on discovery from get_navigation_property.py
Tries multiple property name patterns to handle Dataverse's naming conventions.
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
print("  Create Test Agenda Items - FIXED VERSION")
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
# Test agenda items with special characters
# =============================================================================

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

# =============================================================================
# Try different navigation property patterns
# =============================================================================

# Based on Dataverse conventions, try these patterns in order:
property_patterns = [
    "crad9_Meeting",  # Schema name (PascalCase) - most common
    "crad9_meeting",  # Logical name (lowercase)
    "crad9_meeting_crad9_agendaitem",  # Full relationship name
]

created_count = 0

print("\n" + "=" * 70)
print("Creating Test Agenda Items (Special Characters)")
print("=" * 70)

for agenda in test_agenda_items:
    print(f"\n✓ Creating: {agenda['name']}...")

    # Try each property pattern until one works
    success = False

    for prop_name in property_patterns:
        agenda_payload = {
            "crad9_name": agenda['name'],
            "crad9_sequence": agenda['sequence'],
            "crad9_description": agenda['description'],
            f"{prop_name}@odata.bind": f"/crad9_meetings({meeting_id})",
            "crad9_foldercreated": False
        }

        headers['Content-Type'] = 'application/json'
        create_url = f"{API_URL}/crad9_agendaitems"
        req_data = json.dumps(agenda_payload).encode('utf-8')
        req = urllib.request.Request(create_url, data=req_data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode('utf-8')
                if body:
                    result = json.loads(body)
                    agenda_id = result.get('crad9_agendaitemid', 'created')
                else:
                    agenda_id = 'created (204 No Content)'
                print(f"  ✓ Created with property '{prop_name}': {agenda_id}")
                created_count += 1
                success = True
                break  # Success! Don't try other patterns

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')

            # If it's the "undeclared property" error, try next pattern
            if 'undeclared property' in err_body.lower():
                if prop_name == property_patterns[-1]:  # Last pattern failed
                    print(f"  ✗ All navigation property patterns failed")
                    try:
                        err_json = json.loads(err_body)
                        print(f"    Error: {err_json.get('error', {}).get('message', err_body[:300])}")
                    except:
                        print(f"    Error: {err_body[:300]}")
                continue  # Try next pattern
            else:
                # Different error - report it
                print(f"  ✗ Error (HTTP {e.code}) with property '{prop_name}':")
                try:
                    err_json = json.loads(err_body)
                    print(f"    {err_json.get('error', {}).get('message', err_body[:200])}")
                except:
                    print(f"    {err_body[:200]}")
                break  # Don't try other patterns for non-property errors

    if not success:
        print(f"  ⚠ Skipping '{agenda['name']}' - will need manual creation")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print(f"  ✓ Agenda Items Created: {created_count}/{len(test_agenda_items)}")
print("=" * 70)
print()

if created_count > 0:
    print(f"  Meeting: {meeting_name}")
    print(f"  Successfully created: {created_count} agenda items")
    print()
    print("  Expected Agenda Item Folder Names (sanitized by Power Automate):")
    print("    • Item #1- Budget Review & Approval")
    print("    • Item #2- New Hire (Y-N)")
    print("    • Item #3- Tech Stack- Python-Node.js")
    print("    • Item #4- Client-Server Architecture")
    print("    • Item #5- [URGENT] Security Review")
    print()
    print("  The Power Automate workflows should now:")
    print("    1. Detect the meeting with crad9_isuserallowedspfolder = true")
    print("    2. Create meeting folder in SharePoint (if not created)")
    print("    3. Create subfolders for each agenda item")
    print("    4. Populate crad9_folderurl and crad9_spfolderurl fields")
    print()
    print("  Next: Run test_workflow_execution.py to verify flow execution")
else:
    print("  ✗ No agenda items were created successfully")
    print()
    print("  Possible causes:")
    print("    1. Metadata cache not refreshed - wait 10-15 minutes")
    print("    2. Navigation property name different than expected")
    print("    3. Relationship not properly created")
    print()
    print("  Recommended actions:")
    print("    1. Wait 15 minutes and retry this script")
    print("    2. Run get_navigation_property.py again to re-check")
    print("    3. Check relationship in Power Apps (make.powerapps.com)")
print()
