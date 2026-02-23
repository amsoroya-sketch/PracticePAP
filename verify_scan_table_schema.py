#!/usr/bin/env python3
"""
Verify crad9_scan table schema exists and has all required columns
for the Permission Scanner flow.
"""

import json
import urllib.request
import urllib.parse
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration
# =============================================================================

REQUIRED_COLUMNS = [
    "crad9_scanid",
    "crad9_name",
    "crad9_meeting",
    "crad9_folderurl",
    "crad9_level",
    "crad9_scanstarttime",
    "crad9_scanendtime",
    "crad9_status",
    "crad9_itemsscanned",
    "crad9_brokenpermissionsfound",
    "crad9_totalpermissionsrecorded",
    "crad9_errormessage"
]

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Verify crad9_scan Table Schema")
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
# Check if crad9_scan table exists
# =============================================================================

print("\n✓ Checking if crad9_scan table exists...")

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

# Query entity metadata
entity_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_scan')"
req = urllib.request.Request(urllib.parse.quote(entity_url, safe=':/?=&()'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        entity_meta = json.loads(resp.read().decode('utf-8'))

        print(f"\n  ✓ Table found: crad9_scan")
        print(f"    Schema Name: {entity_meta.get('SchemaName')}")
        print(f"    Display Name: {entity_meta.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
        print(f"    Primary Name: {entity_meta.get('PrimaryNameAttribute')}")

except urllib.error.HTTPError as e:
    if e.code == 404:
        print("\n  ✗ Table 'crad9_scan' does NOT exist")
        print("\n  This table must be created before the Permission Scanner flow can run.")
        print("  The flow requires this table to track scan sessions.")
        sys.exit(1)
    else:
        print(f"\n  ✗ Error: HTTP {e.code}")
        sys.exit(1)

# =============================================================================
# Check required columns
# =============================================================================

print("\n" + "=" * 70)
print("Checking Required Columns")
print("=" * 70)

# Get all attributes
attrs_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_scan')/Attributes?$select=LogicalName,SchemaName,AttributeTypeName,DisplayName"
req = urllib.request.Request(urllib.parse.quote(attrs_url, safe=':/?=&$()'), headers=headers)

with urllib.request.urlopen(req) as resp:
    attrs = json.loads(resp.read().decode('utf-8'))

existing_columns = {attr['LogicalName']: attr for attr in attrs.get('value', [])}

missing_columns = []
found_columns = []

print("\n  Column Check:")
for required_col in REQUIRED_COLUMNS:
    if required_col in existing_columns:
        col = existing_columns[required_col]
        attr_type = col.get('AttributeTypeName', {}).get('Value', 'Unknown')
        display_name = col.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')
        print(f"    ✓ {required_col:35s} ({attr_type:15s}) - {display_name}")
        found_columns.append(required_col)
    else:
        print(f"    ✗ {required_col:35s} MISSING")
        missing_columns.append(required_col)

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  Summary")
print("=" * 70)
print()
print(f"  Table: crad9_scan")
print(f"  Required columns: {len(REQUIRED_COLUMNS)}")
print(f"  Found: {len(found_columns)}")
print(f"  Missing: {len(missing_columns)}")
print()

if missing_columns:
    print("  ✗ SCHEMA INCOMPLETE")
    print("\n  Missing columns that need to be added:")
    for col in missing_columns:
        print(f"    - {col}")
    print()
    print("  Action: These columns must be added to crad9_scan table")
    print("  before the Permission Scanner flow can run.")
    sys.exit(1)
else:
    print("  ✓ SCHEMA COMPLETE")
    print("\n  The crad9_scan table has all required columns.")
    print("  Ready to proceed with creating crad9_itempermission table.")
    print()
