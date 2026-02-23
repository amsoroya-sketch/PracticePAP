#!/usr/bin/env python3
"""
Setup Test Data for Meeting Management Solution

Creates:
1. Meetings library in SharePoint (if permissions allow)
2. Test meetings with special characters to verify API handling
3. Test agenda items with special characters
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import sys
import time
from datetime import datetime, timedelta
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration
# =============================================================================
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"
SITE_URL = f"{SP_ROOT_URL}/sites/Permission-Scanner-Test"
SITE_ALIAS = "Permission-Scanner-Test"
LIBRARY_NAME = "Meetings"

# =============================================================================
# Utility Functions
# =============================================================================

def log(msg):
    print(f"\033[0;34m[INFO]\033[0m  {msg}")

def ok(msg):
    print(f"\033[0;32m[OK]\033[0m    {msg}")

def warn(msg):
    print(f"\033[1;33m[WARN]\033[0m  {msg}")

def error(msg):
    print(f"\033[0;31m[ERROR]\033[0m {msg}")

def get_token(scope):
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': scope
    }).encode('utf-8')

    req = urllib.request.Request(token_url, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8')).get('access_token')

def api_call(method, url, data=None, headers=None):
    if headers is None:
        headers = {}

    req_data = None
    if data:
        req_data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            return {'error': e.code, 'details': err_json}
        except:
            return {'error': e.code, 'details': err_body[:500]}

# =============================================================================
# Main Setup
# =============================================================================

print("\n" + "=" * 70)
print("  Meeting Management Solution - Test Data Setup")
print("=" * 70)

# Step 1: Get tokens
log("Authenticating...")
graph_token = get_token("https://graph.microsoft.com/.default")
sp_token = get_token(f"{SP_ROOT_URL}/.default") or graph_token
dataverse_token = get_token(f"{ORG_URL}/.default")
ok("Authentication successful")

# =============================================================================
# Step 2: Create Meetings Library in SharePoint
# =============================================================================

print("\n" + "=" * 70)
print("STEP 1: SharePoint Library Setup")
print("=" * 70)

log(f"Getting site ID for '{SITE_ALIAS}'...")
site_check_url = f"https://graph.microsoft.com/v1.0/sites/root:/sites/{SITE_ALIAS}"
site_info = api_call("GET", site_check_url, headers={'Authorization': f'Bearer {graph_token}'})

if site_info and 'id' in site_info:
    site_id = site_info['id']
    ok(f"Site ID: {site_id}")
else:
    error("Could not get site information")
    sys.exit(1)

log(f"Checking if '{LIBRARY_NAME}' library exists...")
drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
drives = api_call("GET", drives_url, headers={'Authorization': f'Bearer {graph_token}'})

existing_drive = None
if drives and 'value' in drives:
    for drive in drives['value']:
        if drive.get('name') == LIBRARY_NAME:
            existing_drive = drive
            break

if existing_drive:
    ok(f"Library '{LIBRARY_NAME}' already exists")
    ok(f"Drive ID: {existing_drive.get('id')}")
else:
    log(f"Creating '{LIBRARY_NAME}' library...")
    create_lib_url = f"{SITE_URL}/_api/web/lists"
    lib_payload = {
        "__metadata": {"type": "SP.List"},
        "AllowContentTypes": True,
        "BaseTemplate": 101,
        "ContentTypesEnabled": True,
        "Description": "Meeting documents and agenda item folders",
        "Title": LIBRARY_NAME
    }

    headers = {
        'Authorization': f'Bearer {sp_token}',
        'Content-Type': 'application/json;odata=verbose',
        'Accept': 'application/json;odata=verbose'
    }

    result = api_call("POST", create_lib_url, data=lib_payload, headers=headers)

    if result and 'error' in result:
        warn(f"Could not create library (HTTP {result['error']})")
        warn("Please create the 'Meetings' library manually in SharePoint")
    elif result and result.get('d', {}).get('Title'):
        ok(f"Library '{result['d']['Title']}' created successfully!")
    else:
        warn("Library creation response unclear - may need manual creation")

# =============================================================================
# Step 3: Create Test Meetings in Dataverse
# =============================================================================

print("\n" + "=" * 70)
print("STEP 2: Create Test Meetings in Dataverse")
print("=" * 70)

# Test meeting names with various special characters
test_meetings = [
    {
        "name": "Board Meeting Q1/2026",  # Forward slash
        "level": 1,
        "start": datetime.now() + timedelta(days=7),
        "end": datetime.now() + timedelta(days=7, hours=2),
        "allowed": True
    },
    {
        "name": "Team Sync: Planning & Strategy",  # Colon and ampersand
        "level": 2,
        "start": datetime.now() + timedelta(days=14),
        "end": datetime.now() + timedelta(days=14, hours=1),
        "allowed": True
    },
    {
        "name": "Project Review (2026-Q2)",  # Parentheses and dash
        "level": 2,
        "start": datetime.now() + timedelta(days=21),
        "end": datetime.now() + timedelta(days=21, hours=1.5),
        "allowed": True
    },
    {
        "name": "Budget Meeting?? [Urgent]",  # Question marks and brackets
        "level": 1,
        "start": datetime.now() + timedelta(days=3),
        "end": datetime.now() + timedelta(days=3, hours=2),
        "allowed": True
    },
    {
        "name": "Dev Team\\Backend\\API Review",  # Backslashes
        "level": 3,
        "start": datetime.now() + timedelta(days=10),
        "end": datetime.now() + timedelta(days=10, hours=1),
        "allowed": True
    }
]

created_meetings = []

for i, meeting in enumerate(test_meetings, 1):
    log(f"Creating meeting {i}/5: '{meeting['name']}'...")

    meeting_payload = {
        "crad9_newcolumn": meeting['name'],
        "crad9_level": meeting['level'],
        "crad9_meetingstartdate": meeting['start'].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "crad9_meetingenddate": meeting['end'].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "crad9_isuserallowedspfolder": meeting['allowed'],
        "crad9_spfoldercreated": False
    }

    headers = {
        'Authorization': f'Bearer {dataverse_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Prefer': 'return=representation'
    }

    create_url = f"{API_URL}/crad9_meetings"
    result = api_call("POST", create_url, data=meeting_payload, headers=headers)

    if result and 'error' in result:
        error(f"Failed to create meeting: {result['details']}")
    elif result and 'crad9_meetingid' in result:
        meeting_id = result['crad9_meetingid']
        ok(f"Created: {meeting['name']} (ID: {meeting_id})")
        created_meetings.append({
            'id': meeting_id,
            'name': meeting['name']
        })
    else:
        warn(f"Uncertain result for: {meeting['name']}")

# =============================================================================
# Step 4: Create Test Agenda Items
# =============================================================================

print("\n" + "=" * 70)
print("STEP 3: Create Test Agenda Items")
print("=" * 70)

if created_meetings:
    # Create 2-3 agenda items for the first meeting
    first_meeting = created_meetings[0]

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
        }
    ]

    log(f"Creating agenda items for meeting: {first_meeting['name']}...")

    for agenda in test_agenda_items:
        agenda_payload = {
            "crad9_name": agenda['name'],
            "crad9_sequence": agenda['sequence'],
            "crad9_description": agenda['description'],
            "crad9_Meeting@odata.bind": f"/crad9_meetings({first_meeting['id']})",
            "crad9_foldercreated": False
        }

        create_url = f"{API_URL}/crad9_agendaitems"
        result = api_call("POST", create_url, data=agenda_payload, headers=headers)

        if result and 'error' in result:
            error(f"Failed to create agenda item: {result['details']}")
        elif result and 'crad9_agendaitemid' in result:
            ok(f"Created agenda item: {agenda['name']}")
        else:
            warn(f"Uncertain result for: {agenda['name']}")

# =============================================================================
# Step 5: Wait and verify Power Automate execution
# =============================================================================

print("\n" + "=" * 70)
print("STEP 4: Power Automate Workflow Verification")
print("=" * 70)

log("Waiting 15 seconds for Power Automate workflows to trigger...")
time.sleep(15)

log("Checking if folders were created...")

if created_meetings:
    # Re-fetch first meeting to check if folder URL was populated
    meeting_id = created_meetings[0]['id']
    check_url = f"{API_URL}/crad9_meetings({meeting_id})?$select=crad9_newcolumn,crad9_folderurl,crad9_spfoldercreated"

    headers = {
        'Authorization': f'Bearer {dataverse_token}',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0'
    }

    result = api_call("GET", check_url, headers=headers)

    if result and 'crad9_folderurl' in result:
        folder_url = result.get('crad9_folderurl')
        folder_created = result.get('crad9_spfoldercreated')

        print()
        if folder_url:
            ok(f"Folder URL populated: {folder_url}")
        else:
            warn("Folder URL not yet populated (workflow may still be running)")

        if folder_created:
            ok("SP Folder Created flag = True")
        else:
            warn("SP Folder Created flag = False (workflow may still be running)")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  ✓ TEST DATA SETUP COMPLETE")
print("=" * 70)
print()
print(f"  Meetings Created: {len(created_meetings)}")
print()
print("  Test Meeting Names (Special Characters):")
for meeting in created_meetings:
    print(f"    • {meeting['name']}")
print()
print("  Next Steps:")
print("    1. Check Power Automate flow run history in Power Platform")
print("    2. Verify folders created in SharePoint:")
print(f"       {SITE_URL}/Meetings/")
print("    3. Check for special character handling in folder names")
print("    4. Verify crad9_folderurl field populated in meetings")
print()
print("  Expected folder names (sanitized):")
print("    • Board Meeting Q1-2026")
print("    • Team Sync- Planning & Strategy")
print("    • Project Review (2026-Q2)")
print("    • Budget Meeting [Urgent]")
print("    • Dev Team-Backend-API Review")
print()
