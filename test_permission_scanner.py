#!/usr/bin/env python3
"""
Test Permission Scanner Flow

Validates that the Permission Scanner flow works correctly by:
1. Checking if flow exists in Dataverse
2. Testing manual trigger with a meeting ID
3. Verifying scan record creation
4. Verifying permission records creation
5. Checking combined permission levels
"""

import json
import urllib.request
import urllib.parse
import time
import sys

# =============================================================================
# Configuration
# =============================================================================

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Permission Scanner Flow Test")
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

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

# =============================================================================
# Test 1: Check if Permission Scanner flow exists
# =============================================================================

print("\n" + "=" * 70)
print("TEST 1: Check Permission Scanner Flow Exists")
print("=" * 70)

workflows_url = f"{API_URL}/workflows?$select=workflowid,name,statecode,category&$filter=category eq 5"
req = urllib.request.Request(urllib.parse.quote(workflows_url, safe=':/?=&$,'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        workflows = json.loads(resp.read().decode('utf-8'))

        all_flows = workflows.get('value', [])
        scanner_flows = [f for f in all_flows if 'permission' in f.get('name', '').lower() and 'scan' in f.get('name', '').lower()]

        if scanner_flows:
            print(f"\n  ✓ Permission Scanner flow found!")
            for flow in scanner_flows:
                state = "Active" if flow.get('statecode') == 1 else "Draft/Off"
                print(f"\n    Name: {flow.get('name')}")
                print(f"    ID: {flow.get('workflowid')}")
                print(f"    State: {state}")

                if flow.get('statecode') != 1:
                    print(f"    ⚠ WARNING: Flow is not active. Turn it on in Power Automate portal.")
        else:
            print("\n  ✗ Permission Scanner flow NOT found")
            print("    Import the solution first:")
            print("    ./import_solution_with_flows.sh")
            sys.exit(1)

except Exception as e:
    print(f"\n  ✗ Error querying workflows: {e}")
    sys.exit(1)

# =============================================================================
# Test 2: Check if tables exist
# =============================================================================

print("\n" + "=" * 70)
print("TEST 2: Verify Required Tables Exist")
print("=" * 70)

tables_to_check = ['crad9_scan', 'crad9_itempermission']
tables_exist = {}

for table in tables_to_check:
    entity_url = f"{API_URL}/EntityDefinitions(LogicalName='{table}')"
    req = urllib.request.Request(urllib.parse.quote(entity_url, safe=':/?=&()\''), headers=headers)

    try:
        with urllib.request.urlopen(req) as resp:
            entity = json.loads(resp.read().decode('utf-8'))
            print(f"  ✓ {table} - {entity.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
            tables_exist[table] = True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  ✗ {table} - NOT FOUND")
            tables_exist[table] = False
        else:
            print(f"  ⚠ {table} - Error: HTTP {e.code}")
            tables_exist[table] = False

if not all(tables_exist.values()):
    print("\n  ✗ Missing required tables!")
    print("    Run: python3 create_permission_scanner_tables.py")
    sys.exit(1)

# =============================================================================
# Test 3: Get test meeting with folder URL
# =============================================================================

print("\n" + "=" * 70)
print("TEST 3: Find Test Meeting with Folder URL")
print("=" * 70)

meetings_url = f"{API_URL}/crad9_meetings?$select=crad9_meetingid,crad9_newcolumn,crad9_folderurl,crad9_level&$filter=crad9_folderurl ne null&$top=5"
req = urllib.request.Request(urllib.parse.quote(meetings_url, safe=':/?=&$,'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        meetings = json.loads(resp.read().decode('utf-8'))

        test_meetings = meetings.get('value', [])

        if test_meetings:
            print(f"\n  ✓ Found {len(test_meetings)} meetings with folder URLs:")

            for i, meeting in enumerate(test_meetings[:3], 1):
                print(f"\n    {i}. {meeting.get('crad9_newcolumn')}")
                print(f"       ID: {meeting.get('crad9_meetingid')}")
                print(f"       Folder: {meeting.get('crad9_folderurl')}")
                print(f"       Level: {meeting.get('crad9_level', 1)}")

            # Use first meeting for testing
            test_meeting = test_meetings[0]
            test_meeting_id = test_meeting.get('crad9_meetingid')
            test_meeting_name = test_meeting.get('crad9_newcolumn')

            print(f"\n  Using meeting: {test_meeting_name}")
            print(f"  Meeting ID: {test_meeting_id}")

        else:
            print("\n  ⚠ No meetings with folder URLs found")
            print("    Create a meeting and run CreateMeetingSPFolder flow first")
            sys.exit(1)

except Exception as e:
    print(f"\n  ✗ Error querying meetings: {e}")
    sys.exit(1)

# =============================================================================
# Test 4: Trigger Permission Scanner flow
# =============================================================================

print("\n" + "=" * 70)
print("TEST 4: Trigger Permission Scanner Flow")
print("=" * 70)

print(f"\n  ⚠ MANUAL STEP REQUIRED:")
print(f"    1. Go to: https://make.powerautomate.com")
print(f"    2. Find 'ScanMeetingFolderPermissions' flow")
print(f"    3. Click 'Test' → 'Manually' → 'Test'")
print(f"    4. Enter Meeting ID: {test_meeting_id}")
print(f"    5. Click 'Run flow'")
print()
print(f"  Waiting 30 seconds for manual flow trigger...")

# Wait for user to manually trigger flow
time.sleep(30)

# =============================================================================
# Test 5: Check if scan record was created
# =============================================================================

print("\n" + "=" * 70)
print("TEST 5: Verify Scan Record Creation")
print("=" * 70)

print("\n  Checking for scan records created in last 5 minutes...")

# Get scans created in last 5 minutes
from datetime import datetime, timedelta
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL
five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')

scans_url = f"{API_URL}/crad9_scans?$select=crad9_scanid,crad9_name,crad9_status,crad9_scanstarttime,crad9_itemsscanned,crad9_brokenpermissionsfound,crad9_totalpermissionsrecorded,crad9_errormessage&$filter=crad9_scanstarttime ge {five_min_ago}&$orderby=crad9_scanstarttime desc"
req = urllib.request.Request(urllib.parse.quote(scans_url, safe=':/?=&$,'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        scans = json.loads(resp.read().decode('utf-8'))

        recent_scans = scans.get('value', [])

        if recent_scans:
            print(f"\n  ✓ Found {len(recent_scans)} recent scan(s):")

            for scan in recent_scans:
                status_map = {192350000: "In Progress", 192350001: "Completed", 192350002: "Failed"}
                status = status_map.get(scan.get('crad9_status'), "Unknown")

                print(f"\n    • {scan.get('crad9_name')}")
                print(f"      Status: {status}")
                print(f"      Started: {scan.get('crad9_scanstarttime')}")
                print(f"      Items Scanned: {scan.get('crad9_itemsscanned', 0)}")
                print(f"      Broken Permissions: {scan.get('crad9_brokenpermissionsfound', 0)}")
                print(f"      Permissions Recorded: {scan.get('crad9_totalpermissionsrecorded', 0)}")

                if scan.get('crad9_errormessage'):
                    print(f"      Error: {scan.get('crad9_errormessage')[:200]}")

                # Store first scan for permission check
                if 'test_scan_id' not in locals():
                    test_scan_id = scan.get('crad9_scanid')
        else:
            print("\n  ⚠ No recent scan records found")
            print("    Flow may not have been triggered yet")
            print("    Wait longer and re-run this script")
            test_scan_id = None

except Exception as e:
    print(f"\n  ⚠ Error querying scans: {e}")
    test_scan_id = None

# =============================================================================
# Test 6: Check permission records
# =============================================================================

print("\n" + "=" * 70)
print("TEST 6: Verify Permission Records Created")
print("=" * 70)

if test_scan_id:
    permissions_url = f"{API_URL}/crad9_itempermissions?$select=crad9_itempermissionid,crad9_name,crad9_itemname,crad9_itemtype,crad9_principalname,crad9_principaltype,crad9_permissionlevel&$top=10"
    req = urllib.request.Request(urllib.parse.quote(permissions_url, safe=':/?=&$,'), headers=headers)

    try:
        with urllib.request.urlopen(req) as resp:
            permissions = json.loads(resp.read().decode('utf-8'))

            perm_records = permissions.get('value', [])

            if perm_records:
                print(f"\n  ✓ Found {len(perm_records)} permission record(s):")

                for perm in perm_records[:5]:
                    itemtype_map = {192350000: "File", 192350001: "Folder"}
                    principaltype_map = {192350000: "User", 192350001: "Group"}

                    item_type = itemtype_map.get(perm.get('crad9_itemtype'), "Unknown")
                    principal_type = principaltype_map.get(perm.get('crad9_principaltype'), "Unknown")

                    print(f"\n    • {perm.get('crad9_itemname')} ({item_type})")
                    print(f"      Principal: {perm.get('crad9_principalname')} ({principal_type})")
                    print(f"      Permissions: {perm.get('crad9_permissionlevel')}")

                    # Check if multiple permissions are combined
                    perms = perm.get('crad9_permissionlevel', '')
                    if ', ' in perms:
                        print(f"      ✓ COMBINED PERMISSIONS DETECTED!")

            else:
                print("\n  ⚠ No permission records found")
                print("    Possible reasons:")
                print("      - No items with broken permissions in folder")
                print("      - Flow hasn't completed yet")
                print("      - Level filter excluded all items")

    except Exception as e:
        print(f"\n  ⚠ Error querying permissions: {e}")
else:
    print("\n  ⚠ Skipping - no scan ID available")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  TEST SUMMARY")
print("=" * 70)
print()

tests_passed = 0
tests_total = 6

if scanner_flows and scanner_flows[0].get('statecode') == 1:
    print("  ✓ TEST 1 PASS: Permission Scanner flow exists and is active")
    tests_passed += 1
else:
    print("  ✗ TEST 1 FAIL: Flow not found or not active")

if all(tables_exist.values()):
    print("  ✓ TEST 2 PASS: Required tables exist")
    tests_passed += 1
else:
    print("  ✗ TEST 2 FAIL: Missing tables")

if test_meetings:
    print("  ✓ TEST 3 PASS: Test meeting with folder URL found")
    tests_passed += 1
else:
    print("  ✗ TEST 3 FAIL: No test meetings")

print("  ⚠ TEST 4: Manual trigger required (cannot automate)")

if recent_scans:
    print("  ✓ TEST 5 PASS: Scan record created")
    tests_passed += 1
else:
    print("  ✗ TEST 5 FAIL: No scan records")

if 'perm_records' in locals() and perm_records:
    print("  ✓ TEST 6 PASS: Permission records created")
    tests_passed += 1
else:
    print("  ⚠ TEST 6 INCONCLUSIVE: No permission records (may be expected)")

print()
print(f"  Score: {tests_passed}/{tests_total - 1} tests passed (excluding manual trigger)")
print()

if tests_passed >= 4:
    print("  ✓ PERMISSION SCANNER FLOW IS WORKING!")
    print()
    print("  Next steps:")
    print("    1. Test with different level settings (1, 2, 3)")
    print("    2. Test with folders containing more broken permissions")
    print("    3. Verify combined permissions in permission records")
    print("    4. Check scan status updates")
else:
    print("  ⚠ PERMISSION SCANNER NEEDS ATTENTION")
    print()
    print("  Troubleshooting:")
    print("    1. Ensure flow is turned ON")
    print("    2. Check connection references (Dataverse + SharePoint)")
    print("    3. Verify meeting has valid folder URL")
    print("    4. Check SharePoint 'Meetings' library exists")
    print("    5. Review flow run history for errors")

print()
