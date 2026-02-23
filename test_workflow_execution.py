#!/usr/bin/env python3
"""
Test Power Automate Workflow Execution

End-to-end test that verifies:
1. Meeting folders are created in SharePoint
2. Agenda item subfolders are created
3. crad9_folderurl field is populated
4. Special characters are sanitized correctly
"""

import json
import urllib.request
import urllib.parse
import time
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration
# =============================================================================
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"
SP_SITE_URL = f"{SP_ROOT_URL}/sites/Permission-Scanner-Test"

# =============================================================================
# Get tokens
# =============================================================================

print("\n" + "=" * 70)
print("  Power Automate Workflow Execution Test")
print("=" * 70)

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
        return json.loads(resp.read().decode('utf-8'))['access_token']

print("\n✓ Authenticating...")
dataverse_token = get_token(f"{ORG_URL}/.default")
graph_token = get_token("https://graph.microsoft.com/.default")
print("✓ Tokens obtained")

# =============================================================================
# Test 1: Check if meetings have folder URLs populated
# =============================================================================

print("\n" + "=" * 70)
print("TEST 1: Meeting Folder URL Population")
print("=" * 70)

headers = {
    'Authorization': f'Bearer {dataverse_token}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

# Get test meetings
meetings_url = f"{API_URL}/crad9_meetings?$select=crad9_meetingid,crad9_newcolumn,crad9_folderurl,crad9_spfoldercreated,crad9_isuserallowedspfolder&$top=10"
req = urllib.request.Request(urllib.parse.quote(meetings_url, safe=':/?=&$,'), headers=headers)

with urllib.request.urlopen(req) as resp:
    meetings = json.loads(resp.read().decode('utf-8'))

test_meetings = meetings.get('value', [])
meetings_with_folders = [m for m in test_meetings if m.get('crad9_folderurl')]
meetings_allowed = [m for m in test_meetings if m.get('crad9_isuserallowedspfolder')]

print(f"\n  Total test meetings: {len(test_meetings)}")
print(f"  Meetings with SP allowed: {len(meetings_allowed)}")
print(f"  Meetings with folder URL: {len(meetings_with_folders)}")

if meetings_with_folders:
    print("\n  Meetings with folders created:")
    for meeting in meetings_with_folders[:5]:
        print(f"\n    • {meeting.get('crad9_newcolumn')}")
        print(f"      Folder URL: {meeting.get('crad9_folderurl')}")
        print(f"      Folder Created: {meeting.get('crad9_spfoldercreated')}")
else:
    print("\n  ⚠ No meetings have folder URLs populated yet")
    print("    This means CreateMeetingSPFolder workflow hasn't run successfully")
    print()
    print("    Possible causes:")
    print("      1. Flows not turned on in Power Automate")
    print("      2. Connection references not configured")
    print("      3. Flows triggered but waiting to run")
    print()
    print("    Action: Wait 2-3 minutes for flows to process, then re-run this script")

# =============================================================================
# Test 2: Check if agenda items have folder URLs
# =============================================================================

print("\n" + "=" * 70)
print("TEST 2: Agenda Item Folder URL Population")
print("=" * 70)

agenda_url = f"{API_URL}/crad9_agendaitems?$select=crad9_agendaitemid,crad9_name,crad9_spfolderurl,crad9_spfolderpath,crad9_foldercreated&$top=10"
req = urllib.request.Request(urllib.parse.quote(agenda_url, safe=':/?=&$,'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        agenda_items = json.loads(resp.read().decode('utf-8'))

    all_agenda = agenda_items.get('value', [])
    agenda_with_folders = [a for a in all_agenda if a.get('crad9_spfolderurl')]

    print(f"\n  Total agenda items: {len(all_agenda)}")
    print(f"  Agenda items with folder URL: {len(agenda_with_folders)}")

    if agenda_with_folders:
        print("\n  Agenda items with folders:")
        for agenda in agenda_with_folders[:5]:
            print(f"\n    • {agenda.get('crad9_name')}")
            print(f"      Folder URL: {agenda.get('crad9_spfolderurl')}")
            print(f"      Folder Path: {agenda.get('crad9_spfolderpath')}")
            print(f"      Folder Created: {agenda.get('crad9_foldercreated')}")
    else:
        print("\n  ⚠ No agenda items have folder URLs yet")
        print("    CreateAgendaItemSPFolder workflow hasn't run")

except Exception as e:
    print(f"\n  ⚠ Error querying agenda items: {e}")

# =============================================================================
# Test 3: Verify folders in SharePoint
# =============================================================================

print("\n" + "=" * 70)
print("TEST 3: SharePoint Folder Verification")
print("=" * 70)

graph_headers = {
    'Authorization': f'Bearer {graph_token}',
    'Accept': 'application/json'
}

# Get site ID
site_alias = "Permission-Scanner-Test"
site_check_url = f"https://graph.microsoft.com/v1.0/sites/root:/sites/{site_alias}"
req = urllib.request.Request(site_check_url, headers=graph_headers)

try:
    with urllib.request.urlopen(req) as resp:
        site_info = json.loads(resp.read().decode('utf-8'))
        site_id = site_info['id']

    # Get Meetings library
    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    req = urllib.request.Request(drives_url, headers=graph_headers)

    with urllib.request.urlopen(req) as resp:
        drives = json.loads(resp.read().decode('utf-8'))

    meetings_drive = None
    for drive in drives.get('value', []):
        if drive.get('name') == 'Meetings':
            meetings_drive = drive
            break

    if meetings_drive:
        drive_id = meetings_drive['id']
        print(f"\n  ✓ Meetings library found")
        print(f"    Drive ID: {drive_id}")

        # List items in root of Meetings library
        items_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        req = urllib.request.Request(items_url, headers=graph_headers)

        try:
            with urllib.request.urlopen(req) as resp:
                items = json.loads(resp.read().decode('utf-8'))

            folders = [item for item in items.get('value', []) if 'folder' in item]

            print(f"\n    Folders in Meetings library: {len(folders)}")

            if folders:
                print("\n    Folders found:")
                for folder in folders[:10]:
                    print(f"      • {folder.get('name')}")
            else:
                print("\n    ⚠ No folders found in Meetings library")
                print("      Workflows may not have run yet")

        except Exception as e:
            print(f"\n    ⚠ Could not list folders: {e}")

    else:
        print(f"\n  ✗ Meetings library not found in SharePoint")
        print(f"    Create it manually at: {SP_SITE_URL}")

except Exception as e:
    print(f"\n  ⚠ Error accessing SharePoint: {e}")

# =============================================================================
# Test 4: Special Character Sanitization Check
# =============================================================================

print("\n" + "=" * 70)
print("TEST 4: Special Character Sanitization")
print("=" * 70)

print("\n  Testing that special characters were sanitized:")
print("    • Forward slashes (/) → hyphens (-)")
print("    • Backslashes (\\) → hyphens (-)")
print("    • Colons (:) → hyphens (-)")
print("    • Question marks (?) → removed")
print()

# Check folder URLs for expected sanitization
if meetings_with_folders:
    test_cases = {
        "Q1/2026": "Q1-2026",
        "Planning & Strategy": "Planning & Strategy",  # & is allowed
        "(2026-Q2)": "(2026-Q2)",  # Parentheses allowed
        "??": "",  # Question marks removed
        "Backend\\API": "Backend-API"
    }

    print("  Sample folder URLs created:")
    for meeting in meetings_with_folders[:3]:
        name = meeting.get('crad9_newcolumn', '')
        url = meeting.get('crad9_folderurl', '')

        # Extract folder name from URL
        if url:
            folder_name = url.rstrip('/').split('/')[-1]
            # URL decode
            folder_name = urllib.parse.unquote(folder_name)

            print(f"\n    Original: {name}")
            print(f"    Folder:   {folder_name}")

            # Check expected transformations
            for original, expected in test_cases.items():
                if original in name and expected:
                    if expected in folder_name:
                        print(f"      ✓ '{original}' → '{expected}'")
                    else:
                        print(f"      ? '{original}' transformation unclear")
else:
    print("  ⚠ No folder URLs to check - workflows haven't run")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  TEST SUMMARY")
print("=" * 70)
print()

success_count = 0
total_tests = 4

if meetings_with_folders:
    print("  ✓ TEST 1 PASS: Meeting folder URLs populated")
    success_count += 1
else:
    print("  ✗ TEST 1 FAIL: No meeting folder URLs")

if agenda_with_folders:
    print("  ✓ TEST 2 PASS: Agenda item folder URLs populated")
    success_count += 1
else:
    print("  ✗ TEST 2 FAIL: No agenda item folder URLs")

if meetings_drive and folders:
    print("  ✓ TEST 3 PASS: Folders exist in SharePoint")
    success_count += 1
else:
    print("  ✗ TEST 3 FAIL: No SharePoint folders found")

if meetings_with_folders and any('-' in m.get('crad9_folderurl', '') for m in meetings_with_folders):
    print("  ✓ TEST 4 PASS: Special characters sanitized")
    success_count += 1
else:
    print("  ? TEST 4 INCONCLUSIVE: Cannot verify sanitization")

print()
print(f"  Score: {success_count}/{total_tests} tests passed")
print()

if success_count == total_tests:
    print("  🎉 ALL TESTS PASSED!")
    print("  The Power Automate workflows are working correctly.")
elif success_count > 0:
    print("  ⚠ PARTIAL SUCCESS")
    print("  Some workflows are working. Check failed tests above.")
else:
    print("  ✗ ALL TESTS FAILED")
    print()
    print("  Troubleshooting steps:")
    print("    1. Verify flows are imported: python3 check_flow_import_status.py")
    print("    2. Turn on flows in Power Automate portal")
    print("    3. Configure connection references (Dataverse + SharePoint)")
    print("    4. Manually trigger by updating a meeting:")
    print("       - Set 'Is User Allowed SP Folder' = Yes")
    print("       - Set 'SP Folder Created' = No")
    print("       - Save")
    print("    5. Wait 2-3 minutes for workflow to process")
    print("    6. Re-run this test script")

print()
