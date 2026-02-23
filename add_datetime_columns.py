#!/usr/bin/env python3
"""
Add missing DateTime columns to crad9_scan and crad9_itempermission tables
"""

import json
import urllib.request
import urllib.parse
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration
# =============================================================================

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Add DateTime Columns")
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
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

# =============================================================================
# Add DateTime columns to crad9_scan
# =============================================================================

print("\n✓ Adding DateTime columns to crad9_scan...")

datetime_columns_scan = [
    {
        "LogicalName": "crad9_scanstarttime",
        "SchemaName": "crad9_ScanStartTime",
        "DisplayName": "Scan Start Time",
        "Description": "When the permission scan started",
        "Format": "DateAndTime",
        "DateTimeBehavior": "UserLocal"
    },
    {
        "LogicalName": "crad9_scanendtime",
        "SchemaName": "crad9_ScanEndTime",
        "DisplayName": "Scan End Time",
        "Description": "When the permission scan completed",
        "Format": "DateAndTime",
        "DateTimeBehavior": "UserLocal"
    }
]

for col in datetime_columns_scan:
    attr = {
        "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
        "AttributeType": "DateTime",
        "AttributeTypeName": {"Value": "DateTimeType"},
        "Format": col["Format"],
        "DateTimeBehavior": {
            "Value": col["DateTimeBehavior"]
        },
        "SchemaName": col["SchemaName"],
        "LogicalName": col["LogicalName"],
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": col["DisplayName"],
                    "LanguageCode": 1033
                }
            ]
        },
        "Description": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": col["Description"],
                    "LanguageCode": 1033
                }
            ]
        },
        "RequiredLevel": {
            "Value": "None"
        }
    }

    url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_scan')/Attributes"
    req_data = json.dumps(attr).encode('utf-8')
    req = urllib.request.Request(url, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  ✓ {col['SchemaName']}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"  ✗ {col['SchemaName']}: {err_body[:150]}")

# =============================================================================
# Add DateTime column to crad9_itempermission
# =============================================================================

print("\n✓ Adding DateTime column to crad9_itempermission...")

scanned_at_col = {
    "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
    "AttributeType": "DateTime",
    "AttributeTypeName": {"Value": "DateTimeType"},
    "Format": "DateAndTime",
    "DateTimeBehavior": {
        "Value": "UserLocal"
    },
    "SchemaName": "crad9_ScannedAt",
    "LogicalName": "crad9_scannedat",
    "DisplayName": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [
            {
                "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                "Label": "Scanned At",
                "LanguageCode": 1033
            }
        ]
    },
    "Description": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [
            {
                "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                "Label": "When this permission was recorded",
                "LanguageCode": 1033
            }
        ]
    },
    "RequiredLevel": {
        "Value": "None"
    }
}

url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_itempermission')/Attributes"
req_data = json.dumps(scanned_at_col).encode('utf-8')
req = urllib.request.Request(url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print(f"  ✓ crad9_ScannedAt")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f"  ✗ crad9_ScannedAt: {err_body[:150]}")

# =============================================================================
# Add Scan lookup relationship to crad9_itempermission
# =============================================================================

print("\n✓ Adding Scan lookup relationship to crad9_itempermission...")

scan_relationship = {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_Scan_crad9_ItemPermission",
    "ReferencedEntity": "crad9_scan",
    "ReferencingEntity": "crad9_itempermission",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Scan",
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "Scan",
                    "LanguageCode": 1033
                }
            ]
        },
        "RequiredLevel": {
            "Value": "None"
        },
        "Description": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "The scan session that discovered this permission",
                    "LanguageCode": 1033
                }
            ]
        }
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

url = f"{API_URL}/RelationshipDefinitions"
req_data = json.dumps(scan_relationship).encode('utf-8')
req = urllib.request.Request(url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("  ✓ Scan relationship created")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    if 'already exists' in err_body.lower():
        print("  ✓ Scan relationship already exists")
    else:
        print(f"  ⚠ Scan relationship: {err_body[:200]}")

# =============================================================================
# Publish customizations
# =============================================================================

print("\n✓ Publishing customizations...")

publish_url = f"{API_URL}/PublishAllXml"
publish_req = urllib.request.Request(publish_url, data=b'{}', headers=headers, method='POST')

try:
    with urllib.request.urlopen(publish_req) as resp:
        print("✓ Customizations published")
except Exception as e:
    print(f"⚠ Publish warning: {e}")

print("\n" + "=" * 70)
print("  ✓ DateTime Columns Added!")
print("=" * 70)
print("\n  Next: Run verify_scan_table_schema.py to confirm all columns exist")
print()
