#!/usr/bin/env python3
"""
Dataverse Schema Verification Script

Verifies that all schema changes were successfully applied:
- crad9_meeting: 5 new columns
- crad9_agendaitem: new table with 6 columns
- crad9_meetingcontact: new table with 3 columns
"""

import json
import urllib.request
import urllib.parse
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration (from MSDev .env)
# =============================================================================

# =============================================================================
# Utility functions
# =============================================================================

def get_token():
    """Get OAuth2 access token for Dataverse"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': f'{ORG_URL}/.default'
    }).encode('utf-8')

    req = urllib.request.Request(token_url, data=data)
    with urllib.request.urlopen(req) as resp:
        token_resp = json.loads(resp.read().decode('utf-8'))
        return token_resp['access_token']

def api_call(method, endpoint, token):
    """Make an API call to Dataverse"""
    url = f"{API_URL}/{endpoint}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0'
    }

    req = urllib.request.Request(urllib.parse.quote(url, safe=':/?=&'), headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return None

# =============================================================================
# Main Verification
# =============================================================================

print("\n" + "=" * 60)
print("  Dataverse Schema Verification")
print("  Org:", ORG_URL)
print("=" * 60)

TOKEN = get_token()
print("\n✓ Authentication successful\n")

# 1. Verify crad9_meeting extended columns
print("=" * 60)
print("1. Verifying crad9_meeting extended columns")
print("=" * 60)

meeting_attrs = api_call("GET", "EntityDefinitions(LogicalName='crad9_meeting')/Attributes?$filter=LogicalName eq 'crad9_level' or LogicalName eq 'crad9_meetingstartdate' or LogicalName eq 'crad9_meetingenddate' or LogicalName eq 'crad9_isuserallowedspfolder' or LogicalName eq 'crad9_spfoldercreated'", TOKEN)

if meeting_attrs and 'value' in meeting_attrs:
    for attr in meeting_attrs['value']:
        print(f"  ✓ {attr['LogicalName']:30s} ({attr['@odata.type'].split('.')[-1]})")
    print(f"\n  Total: {len(meeting_attrs['value'])}/5 columns found")
else:
    print("  ✗ Could not retrieve crad9_meeting attributes")

# 2. Verify crad9_agendaitem table
print("\n" + "=" * 60)
print("2. Verifying crad9_agendaitem table")
print("=" * 60)

agenda_entity = api_call("GET", "EntityDefinitions(LogicalName='crad9_agendaitem')?$select=LogicalName,DisplayName,PrimaryNameAttribute", TOKEN)

if agenda_entity:
    print(f"  ✓ Table: {agenda_entity['LogicalName']}")
    print(f"  ✓ Display Name: {agenda_entity.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
    print(f"  ✓ Primary Name: {agenda_entity.get('PrimaryNameAttribute')}")

    # Get attributes
    agenda_attrs = api_call("GET", "EntityDefinitions(LogicalName='crad9_agendaitem')/Attributes?$select=LogicalName,AttributeType", TOKEN)

    if agenda_attrs and 'value' in agenda_attrs:
        print(f"\n  Attributes ({len(agenda_attrs['value'])} total):")
        custom_attrs = [a for a in agenda_attrs['value'] if a['LogicalName'].startswith('crad9_')]
        for attr in sorted(custom_attrs, key=lambda x: x['LogicalName']):
            print(f"    - {attr['LogicalName']:30s} ({attr.get('AttributeType', 'Unknown')})")
else:
    print("  ✗ crad9_agendaitem table not found")

# 3. Verify crad9_meetingcontact table
print("\n" + "=" * 60)
print("3. Verifying crad9_meetingcontact table")
print("=" * 60)

mc_entity = api_call("GET", "EntityDefinitions(LogicalName='crad9_meetingcontact')?$select=LogicalName,DisplayName,PrimaryNameAttribute", TOKEN)

if mc_entity:
    print(f"  ✓ Table: {mc_entity['LogicalName']}")
    print(f"  ✓ Display Name: {mc_entity.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
    print(f"  ✓ Primary Name: {mc_entity.get('PrimaryNameAttribute')}")

    # Get attributes
    mc_attrs = api_call("GET", "EntityDefinitions(LogicalName='crad9_meetingcontact')/Attributes?$select=LogicalName,AttributeType", TOKEN)

    if mc_attrs and 'value' in mc_attrs:
        print(f"\n  Attributes ({len(mc_attrs['value'])} total):")
        custom_attrs = [a for a in mc_attrs['value'] if a['LogicalName'].startswith('crad9_')]
        for attr in sorted(custom_attrs, key=lambda x: x['LogicalName']):
            print(f"    - {attr['LogicalName']:30s} ({attr.get('AttributeType', 'Unknown')})")
else:
    print("  ✗ crad9_meetingcontact table not found")

# 4. Summary
print("\n" + "=" * 60)
print("  Verification Complete")
print("=" * 60)
print()
