#!/usr/bin/env python3
"""
Discover the correct navigation property name for the Meeting lookup in Agenda Item table.

This solves the "undeclared property 'crad9_meeting'" error by finding the exact
property name to use in @odata.bind syntax.
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
print("  Navigation Property Discovery")
print("  Finding correct property name for Meeting lookup in Agenda Item")
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
# Method 1: Query ManyToOne relationships from entity metadata
# =============================================================================

print("\n" + "=" * 70)
print("METHOD 1: Entity Metadata - ManyToOneRelationships")
print("=" * 70)

entity_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_agendaitem')?$select=LogicalName&$expand=ManyToOneRelationships($filter=ReferencedEntity eq 'crad9_meeting')"
headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

req = urllib.request.Request(urllib.parse.quote(entity_url, safe=':/?=&$,()'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        entity_meta = json.loads(resp.read().decode('utf-8'))

        if 'ManyToOneRelationships' in entity_meta and entity_meta['ManyToOneRelationships']:
            for rel in entity_meta['ManyToOneRelationships']:
                print(f"\n  Relationship: {rel.get('SchemaName')}")
                print(f"    Referenced Entity: {rel.get('ReferencedEntity')}")
                print(f"    Referencing Attribute: {rel.get('ReferencingAttribute')}")
                print(f"    ✓ Navigation Property: {rel.get('ReferencingEntityNavigationPropertyName')}")

                nav_prop = rel.get('ReferencingEntityNavigationPropertyName')
                if nav_prop:
                    print(f"\n  {'='*70}")
                    print(f"  FOUND IT! Use this in your @odata.bind:")
                    print(f"  {'='*70}")
                    print(f"  \"{nav_prop}@odata.bind\": \"/crad9_meetings({{meeting_id}})\"")
                    print(f"  {'='*70}")
        else:
            print("\n  No ManyToOne relationships found to crad9_meeting")
except Exception as e:
    print(f"  Error: {e}")

# =============================================================================
# Method 2: Query relationship definitions directly
# =============================================================================

print("\n" + "=" * 70)
print("METHOD 2: Relationship Definitions")
print("=" * 70)

# Get all relationships where AgendaItem is the referencing entity
rel_url = f"{API_URL}/RelationshipDefinitions"
req = urllib.request.Request(urllib.parse.quote(rel_url, safe=':/?=&()'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        all_rels = json.loads(resp.read().decode('utf-8'))

        # Filter for our specific relationship
        meeting_rels = [
            r for r in all_rels.get('value', [])
            if r.get('ReferencingEntity') == 'crad9_agendaitem'
            and r.get('ReferencedEntity') == 'crad9_meeting'
        ]

        if meeting_rels:
            for rel in meeting_rels:
                print(f"\n  Relationship Schema Name: {rel.get('SchemaName')}")
                print(f"    Referencing Entity: {rel.get('ReferencingEntity')}")
                print(f"    Referenced Entity: {rel.get('ReferencedEntity')}")
                print(f"    Referencing Attribute: {rel.get('ReferencingAttribute')}")

                # The navigation property might be in different locations depending on type
                if rel.get('@odata.type') == 'Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata':
                    nav_prop = rel.get('ReferencingEntityNavigationPropertyName')
                    if nav_prop:
                        print(f"    ✓ Navigation Property (Referencing): {nav_prop}")
        else:
            print("\n  No matching relationships found")

except Exception as e:
    print(f"  Error: {e}")

# =============================================================================
# Method 3: Check lookup attribute metadata
# =============================================================================

print("\n" + "=" * 70)
print("METHOD 3: Lookup Attribute Metadata")
print("=" * 70)

attr_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_agendaitem')/Attributes(LogicalName='crad9_meeting')"
req = urllib.request.Request(urllib.parse.quote(attr_url, safe=':/?=&()'), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        lookup_attr = json.loads(resp.read().decode('utf-8'))

        print(f"\n  Lookup Field Information:")
        print(f"    Logical Name: {lookup_attr.get('LogicalName')}")
        print(f"    Schema Name: {lookup_attr.get('SchemaName')}")
        print(f"    Display Name: {lookup_attr.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
        print(f"    Targets: {lookup_attr.get('Targets')}")

        # Navigation property info might be here
        if 'NavigationPropertyName' in lookup_attr:
            print(f"    ✓ Navigation Property: {lookup_attr.get('NavigationPropertyName')}")

except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"\n  Attribute 'crad9_meeting' not found - metadata may not be refreshed yet")
    else:
        print(f"  HTTP Error {e.code}: {e.read().decode('utf-8')[:200]}")
except Exception as e:
    print(f"  Error: {e}")

# =============================================================================
# Summary & Recommendation
# =============================================================================

print("\n" + "=" * 70)
print("  SUMMARY & NEXT STEPS")
print("=" * 70)
print()
print("  Based on the discovery above, update your agenda item creation code:")
print()
print("  BEFORE (incorrect):")
print('    "crad9_meeting@odata.bind": "/crad9_meetings({meeting_id})"')
print()
print("  AFTER (correct - use the navigation property shown above):")
print('    "{NavigationPropertyName}@odata.bind": "/crad9_meetings({meeting_id})"')
print()
print("  Common navigation property patterns for lookup fields:")
print("    • Exact schema name: crad9_Meeting")
print("    • Full relationship name: crad9_meeting_crad9_agendaitem")
print("    • Logical name: crad9_meeting (rare for navigation)")
print()
print("  If no navigation property found, the relationship may need more time")
print("  to propagate. Wait 5-10 minutes and run this script again.")
print()
