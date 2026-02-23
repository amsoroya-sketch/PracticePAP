#!/usr/bin/env python3
"""
Add Meeting lookup field to Agenda Item table with proper relationship
"""

import json
import urllib.request
import urllib.parse
import time
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Add Meeting Lookup to Agenda Item")
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
# Create One-to-Many Relationship (Meeting -> Agenda Items)
# =============================================================================

print("\n✓ Creating Meeting -> Agenda Item relationship...")

relationship_def = {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_Meeting_crad9_AgendaItem",
    "ReferencedEntity": "crad9_meeting",
    "ReferencingEntity": "crad9_agendaitem",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "AttributeType": "Lookup",
        "AttributeTypeName": {
            "Value": "LookupType"
        },
        "SchemaName": "crad9_Meeting",
        "LogicalName": "crad9_meeting",
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "Meeting",
                    "LanguageCode": 1033
                }
            ]
        },
        "Description": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "Parent meeting for this agenda item",
                    "LanguageCode": 1033
                }
            ]
        },
        "RequiredLevel": {
            "Value": "ApplicationRequired",
            "CanBeChanged": True
        }
    },
    "AssociatedMenuConfiguration": {
        "Behavior": "UseCollectionName",
        "Group": "Details",
        "Label": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "Agenda Items",
                    "LanguageCode": 1033
                }
            ]
        },
        "Order": 10000
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade",
        "Delete": "Cascade",
        "Merge": "NoCascade",
        "Reparent": "NoCascade",
        "Share": "NoCascade",
        "Unshare": "NoCascade"
    }
}

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

create_url = f"{API_URL}/RelationshipDefinitions"
req_data = json.dumps(relationship_def).encode('utf-8')
req = urllib.request.Request(create_url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("✓ Relationship created successfully!")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    try:
        err_json = json.loads(err_body)
        if 'already exists' in err_json.get('error', {}).get('message', '').lower():
            print("✓ Relationship already exists")
        else:
            print(f"\n✗ Error creating relationship (HTTP {e.code}):")
            print(json.dumps(err_json, indent=2))
            sys.exit(1)
    except:
        print(f"\n✗ Error: {err_body[:500]}")
        sys.exit(1)

# =============================================================================
# Publish customizations
# =============================================================================

print("\n✓ Publishing customizations...")
time.sleep(3)

publish_url = f"{API_URL}/PublishAllXml"
req = urllib.request.Request(publish_url, data=b'{}', headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("\n" + "=" * 70)
        print("  ✓ Lookup Field Added Successfully!")
        print("=" * 70)
        print()
        print("  crad9_agendaitem.crad9_meeting (Lookup)")
        print("    → References crad9_meeting table")
        print("    → Required field")
        print("    → Cascade delete enabled")
        print()
        print("  You can now create agenda items with:")
        print('    "crad9_meeting@odata.bind": "/crad9_meetings(meeting-id)"')
        print()
except Exception as e:
    print(f"  Warning: Publish may have failed: {e}")

print()
