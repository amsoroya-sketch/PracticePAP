#!/usr/bin/env python3
"""
Check the actual lookup field name for the Meeting relationship in Agenda Item table
"""

import json
import urllib.request
import urllib.parse
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL


# Get token
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

print("\n" + "=" * 70)
print("  Checking crad9_agendaitem Lookup Fields")
print("=" * 70)

# Get all attributes (we'll filter for lookups manually)
attrs_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_agendaitem')/Attributes"
headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

req = urllib.request.Request(urllib.parse.quote(attrs_url, safe=':/?=&()'), headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        attrs = json.loads(resp.read().decode('utf-8'))

        print("\nLookup fields found:")
        if 'value' in attrs:
            lookup_attrs = [a for a in attrs['value'] if 'Lookup' in a.get('@odata.type', '')]
            for attr in lookup_attrs:
                print(f"\n  Field: {attr.get('LogicalName')}")
                print(f"    Schema Name: {attr.get('SchemaName')}")
                print(f"    Display Name: {attr.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
                print(f"    Type: {attr.get('@odata.type', 'N/A').split('.')[-1]}")

                # Get relationship details
                if 'Targets' in attr:
                    print(f"    Targets: {attr.get('Targets')}")
        else:
            print("  No lookup fields found")

except Exception as e:
    print(f"Error: {e}")

# Also check relationships
print("\n" + "=" * 70)
print("  Checking Relationships")
print("=" * 70)

rel_url = f"{API_URL}/RelationshipDefinitions"
req = urllib.request.Request(urllib.parse.quote(rel_url, safe=':/?=&()'), headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        rels = json.loads(resp.read().decode('utf-8'))

        print("\nRelationships found:")
        if 'value' in rels:
            agenda_rels = [r for r in rels['value'] if r.get('ReferencingEntity') == 'crad9_agendaitem']
            for rel in agenda_rels:
                print(f"\n  Relationship: {rel.get('SchemaName')}")
                print(f"    Type: {rel.get('@odata.type', 'N/A').split('.')[-1]}")
                print(f"    Referencing Entity: {rel.get('ReferencingEntity')}")
                print(f"    Referenced Entity: {rel.get('ReferencedEntity')}")
                print(f"    Referencing Attribute: {rel.get('ReferencingAttribute')}")
        else:
            print("  No relationships found")

except Exception as e:
    print(f"Error: {e}")

print()
