#!/usr/bin/env python3
"""
Check Power Automate Flow Import Status

Verifies that CreateMeetingSPFolder and CreateAgendaItemSPFolder flows
were successfully imported to Dataverse via solution import.
"""

import json
import urllib.request
import urllib.parse
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration
# =============================================================================

EXPECTED_FLOWS = [
    "CreateMeetingSPFolder",
    "CreateAgendaItemSPFolder"
]

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Power Automate Flow Import Status Check")
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
# Query workflows (Power Automate flows are stored as workflows in Dataverse)
# =============================================================================

print("\n✓ Querying workflows...")

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

# Workflows table query
# Category = 5 for Modern Flows (Power Automate cloud flows)
workflows_url = f"{API_URL}/workflows?$select=workflowid,name,statecode,statuscode,category,type&$filter=category eq 5"
req = urllib.request.Request(urllib.parse.quote(workflows_url, safe=':/?=&$,'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        workflows = json.loads(resp.read().decode('utf-8'))

        all_flows = workflows.get('value', [])

        print(f"\n  Total cloud flows found: {len(all_flows)}")

        # Check for our specific flows
        found_flows = []
        for flow_name in EXPECTED_FLOWS:
            matching = [f for f in all_flows if flow_name.lower() in f.get('name', '').lower()]
            if matching:
                found_flows.extend(matching)

        print("\n" + "=" * 70)
        print("Expected Flows Status")
        print("=" * 70)

        for expected_name in EXPECTED_FLOWS:
            matching = [f for f in found_flows if expected_name.lower() in f.get('name', '').lower()]

            if matching:
                flow = matching[0]
                state = "Active" if flow.get('statecode') == 1 else "Draft/Off"
                status_code = flow.get('statuscode')

                print(f"\n  ✓ {flow.get('name')}")
                print(f"    ID: {flow.get('workflowid')}")
                print(f"    State: {state} (statecode: {flow.get('statecode')})")
                print(f"    Status: {status_code}")
                print(f"    Type: {flow.get('type')}")

                if flow.get('statecode') != 1:
                    print(f"    ⚠ WARNING: Flow is not active. Turn it on in Power Automate portal.")
            else:
                print(f"\n  ✗ {expected_name}")
                print(f"    NOT FOUND - May need to import solution or wait for sync")

        # Show other flows for reference
        other_flows = [f for f in all_flows if f not in found_flows]
        if other_flows:
            print("\n" + "=" * 70)
            print(f"Other Flows in Environment ({len(other_flows)} total)")
            print("=" * 70)
            for flow in other_flows[:5]:  # Show first 5
                print(f"  • {flow.get('name')} (state: {flow.get('statecode')})")

except urllib.error.HTTPError as e:
    print(f"\n  ✗ Error querying workflows (HTTP {e.code})")
    err_body = e.read().decode('utf-8')
    try:
        err_json = json.loads(err_body)
        print(f"    {err_json.get('error', {}).get('message', err_body[:300])}")
    except:
        print(f"    {err_body[:300]}")
    sys.exit(1)

# =============================================================================
# Check solution components
# =============================================================================

print("\n" + "=" * 70)
print("Solution Component Check")
print("=" * 70)

# Query solution
solution_url = f"{API_URL}/solutions?$select=solutionid,uniquename,version,friendlyname&$filter=uniquename eq 'CRMPowerBISharePointIntegration'"
req = urllib.request.Request(urllib.parse.quote(solution_url, safe=':/?=&$,'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        solutions = json.loads(resp.read().decode('utf-8'))

        if solutions.get('value'):
            solution = solutions['value'][0]
            print(f"\n  ✓ Solution: {solution.get('friendlyname')}")
            print(f"    Unique Name: {solution.get('uniquename')}")
            print(f"    Version: {solution.get('version')}")
            print(f"    ID: {solution.get('solutionid')}")

            # Query components in this solution
            solution_id = solution.get('solutionid')
            components_url = f"{API_URL}/solutioncomponents?$select=componenttype,objectid&$filter=_solutionid_value eq {solution_id} and componenttype eq 29"
            req2 = urllib.request.Request(urllib.parse.quote(components_url, safe=':/?=&$,'), headers=headers)

            try:
                with urllib.request.urlopen(req2) as resp2:
                    components = json.loads(resp2.read().decode('utf-8'))

                    workflow_components = components.get('value', [])
                    print(f"\n    Workflow components in solution: {len(workflow_components)}")

                    if len(workflow_components) > 0:
                        print(f"    ✓ Solution contains workflows")
                    else:
                        print(f"    ⚠ No workflow components found (componenttype 29)")

            except Exception as e:
                print(f"    ⚠ Could not query solution components: {e}")

        else:
            print(f"\n  ✗ Solution 'CRMPowerBISharePointIntegration' not found")
            print(f"    Run import_solution_with_flows.sh to import")

except Exception as e:
    print(f"\n  ✗ Error querying solution: {e}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  Summary")
print("=" * 70)
print()

if len(found_flows) == len(EXPECTED_FLOWS):
    print("  ✓ All expected flows found in environment")
    print()
    print("  Next steps:")
    print("    1. Turn on flows in Power Automate portal (if off)")
    print("    2. Configure connection references")
    print("    3. Run test_workflow_execution.py to test")
elif len(found_flows) > 0:
    print(f"  ⚠ Partial import: {len(found_flows)}/{len(EXPECTED_FLOWS)} flows found")
    print()
    print("  Missing flows - check import logs")
else:
    print("  ✗ No expected flows found")
    print()
    print("  Action required:")
    print("    Run: ./import_solution_with_flows.sh")

print()
