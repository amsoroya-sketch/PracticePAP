#!/usr/bin/env python3
"""
Create Dataverse tables required for Permission Scanner flow:
1. crad9_scan - Tracks permission scan sessions
2. crad9_itempermission - Stores individual item permissions

Uses Dataverse Web API to create tables with all required columns and relationships.
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

# =============================================================================
# Get token
# =============================================================================

print("\n" + "=" * 70)
print("  Create Permission Scanner Tables")
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
# Create crad9_scan table
# =============================================================================

print("\n" + "=" * 70)
print("Creating crad9_scan Table")
print("=" * 70)

scan_entity = {
    "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
    "SchemaName": "crad9_Scan",
    "LogicalName": "crad9_scan",
    "DisplayName": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Permission Scan", "LanguageCode": 1033}]
    },
    "DisplayCollectionName": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Permission Scans", "LanguageCode": 1033}]
    },
    "Description": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Tracks SharePoint permission scan sessions for meetings", "LanguageCode": 1033}]
    },
    "OwnershipType": "UserOwned",
    "IsActivity": False,
    "HasActivities": False,
    "HasNotes": False,
    "PrimaryNameAttribute": "crad9_name",
    "Attributes": [
        {
            "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
            "SchemaName": "crad9_name",
            "LogicalName": "crad9_name",
            "IsPrimaryName": True,
            "DisplayName": {
                "@odata.type": "Microsoft.Dynamics.CRM.Label",
                "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Scan Name", "LanguageCode": 1033}]
            },
            "RequiredLevel": {"Value": "ApplicationRequired"},
            "MaxLength": 255,
            "Format": "Text",
            "Description": {
                "@odata.type": "Microsoft.Dynamics.CRM.Label",
                "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Name of the permission scan session", "LanguageCode": 1033}]
            }
        }
    ]
}

create_url = f"{API_URL}/EntityDefinitions"
req_data = json.dumps(scan_entity).encode('utf-8')
req = urllib.request.Request(create_url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("\n✓ crad9_scan table created")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    if 'already exists' in err_body.lower():
        print("\n✓ crad9_scan table already exists")
    else:
        print(f"\n✗ Error creating table: HTTP {e.code}")
        print(err_body[:500])
        sys.exit(1)

# Wait for table to provision
print("  Waiting 8 seconds for table provisioning...")
time.sleep(8)

# =============================================================================
# Add columns to crad9_scan
# =============================================================================

print("\n✓ Adding columns to crad9_scan...")

scan_columns = [
    {
        "name": "crad9_FolderURL",
        "type": "StringAttributeMetadata",
        "maxLength": 500,
        "format": "Url",
        "display": "Folder URL",
        "description": "SharePoint folder URL being scanned"
    },
    {
        "name": "crad9_Level",
        "type": "IntegerAttributeMetadata",
        "format": "None",
        "display": "Level",
        "description": "Minimum folder depth level to scan"
    },
    {
        "name": "crad9_ScanStartTime",
        "type": "DateTimeAttributeMetadata",
        "format": "DateAndTime",
        "behavior": 1,
        "display": "Scan Start Time",
        "description": "When the scan started"
    },
    {
        "name": "crad9_ScanEndTime",
        "type": "DateTimeAttributeMetadata",
        "format": "DateAndTime",
        "behavior": 1,
        "display": "Scan End Time",
        "description": "When the scan completed"
    },
    {
        "name": "crad9_Status",
        "type": "PicklistAttributeMetadata",
        "options": [
            {"Value": 1, "Label": "In Progress"},
            {"Value": 2, "Label": "Completed"},
            {"Value": 3, "Label": "Failed"}
        ],
        "display": "Status",
        "description": "Current status of the scan"
    },
    {
        "name": "crad9_ItemsScanned",
        "type": "IntegerAttributeMetadata",
        "format": "None",
        "display": "Items Scanned",
        "description": "Total number of items scanned"
    },
    {
        "name": "crad9_BrokenPermissionsFound",
        "type": "IntegerAttributeMetadata",
        "format": "None",
        "display": "Broken Permissions Found",
        "description": "Number of items with unique permissions"
    },
    {
        "name": "crad9_TotalPermissionsRecorded",
        "type": "IntegerAttributeMetadata",
        "format": "None",
        "display": "Total Permissions Recorded",
        "description": "Total permission records created"
    },
    {
        "name": "crad9_ErrorMessage",
        "type": "MemoAttributeMetadata",
        "format": "Text",
        "maxLength": 10000,
        "display": "Error Message",
        "description": "Error details if scan failed"
    }
]

for col in scan_columns:
    col_def = {
        "@odata.type": f"Microsoft.Dynamics.CRM.{col['type']}",
        "AttributeType": col['type'].replace('AttributeMetadata', '').replace('Metadata', ''),
        "SchemaName": col['name'],
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": col['display'], "LanguageCode": 1033}]
        },
        "Description": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": col['description'], "LanguageCode": 1033}]
        },
        "RequiredLevel": {"Value": "None"}
    }

    if col['type'] == 'StringAttributeMetadata':
        col_def["AttributeTypeName"] = {"Value": "StringType"}
        col_def["MaxLength"] = col['maxLength']
        if 'format' in col:
            col_def["Format"] = col['format']
    elif col['type'] == 'IntegerAttributeMetadata':
        col_def["Format"] = col['format']
        col_def["MinValue"] = 0
        col_def["MaxValue"] = 2147483647
    elif col['type'] == 'DateTimeAttributeMetadata':
        col_def["Format"] = col['format']
        col_def["Behavior"] = col['behavior']
    elif col['type'] == 'PicklistAttributeMetadata':
        col_def["OptionSet"] = {
            "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
            "Options": [
                {
                    "Value": opt["Value"],
                    "Label": {
                        "@odata.type": "Microsoft.Dynamics.CRM.Label",
                        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": opt["Label"], "LanguageCode": 1033}]
                    }
                } for opt in col['options']
            ],
            "IsGlobal": False,
            "OptionSetType": "Picklist"
        }
    elif col['type'] == 'MemoAttributeMetadata':
        col_def["Format"] = col['format']
        col_def["MaxLength"] = col['maxLength']

    col_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_scan')/Attributes"
    req_data = json.dumps(col_def).encode('utf-8')
    req = urllib.request.Request(col_url, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  ✓ {col['name']}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        if 'already exists' in err_body.lower():
            print(f"  ✓ {col['name']} (already exists)")
        else:
            print(f"  ✗ {col['name']}: {err_body[:200]}")

# Add Meeting lookup
print("\n✓ Adding Meeting lookup to crad9_scan...")

meeting_relationship = {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_Meeting_crad9_Scan",
    "ReferencedEntity": "crad9_meeting",
    "ReferencingEntity": "crad9_scan",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "AttributeType": "Lookup",
        "AttributeTypeName": {"Value": "LookupType"},
        "SchemaName": "crad9_Meeting",
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Meeting", "LanguageCode": 1033}]
        },
        "RequiredLevel": {"Value": "ApplicationRequired"}
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

rel_url = f"{API_URL}/RelationshipDefinitions"
req_data = json.dumps(meeting_relationship).encode('utf-8')
req = urllib.request.Request(rel_url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("  ✓ Meeting relationship created")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    if 'already exists' in err_body.lower():
        print("  ✓ Meeting relationship already exists")
    else:
        print(f"  ⚠ Meeting relationship: {err_body[:200]}")

# =============================================================================
# Create crad9_itempermission table
# =============================================================================

print("\n" + "=" * 70)
print("Creating crad9_itempermission Table")
print("=" * 70)

perm_entity = {
    "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
    "SchemaName": "crad9_ItemPermission",
    "LogicalName": "crad9_itempermission",
    "DisplayName": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Item Permission", "LanguageCode": 1033}]
    },
    "DisplayCollectionName": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Item Permissions", "LanguageCode": 1033}]
    },
    "Description": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Stores SharePoint item permissions discovered during scans", "LanguageCode": 1033}]
    },
    "OwnershipType": "UserOwned",
    "IsActivity": False,
    "HasActivities": False,
    "HasNotes": False,
    "PrimaryNameAttribute": "crad9_name",
    "Attributes": [
        {
            "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
            "SchemaName": "crad9_name",
            "LogicalName": "crad9_name",
            "IsPrimaryName": True,
            "DisplayName": {
                "@odata.type": "Microsoft.Dynamics.CRM.Label",
                "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Name", "LanguageCode": 1033}]
            },
            "RequiredLevel": {"Value": "ApplicationRequired"},
            "MaxLength": 255,
            "Format": "Text"
        }
    ]
}

req_data = json.dumps(perm_entity).encode('utf-8')
req = urllib.request.Request(create_url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("\n✓ crad9_itempermission table created")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    if 'already exists' in err_body.lower():
        print("\n✓ crad9_itempermission table already exists")
    else:
        print(f"\n✗ Error: {err_body[:500]}")
        sys.exit(1)

print("  Waiting 8 seconds for table provisioning...")
time.sleep(8)

# =============================================================================
# Add columns to crad9_itempermission
# =============================================================================

print("\n✓ Adding columns to crad9_itempermission...")

perm_columns = [
    {"name": "crad9_ItemURL", "type": "StringAttributeMetadata", "maxLength": 500, "display": "Item URL", "desc": "SharePoint item URL"},
    {"name": "crad9_ItemName", "type": "StringAttributeMetadata", "maxLength": 255, "display": "Item Name", "desc": "File or folder name"},
    {"name": "crad9_ItemType", "type": "PicklistAttributeMetadata", "options": [{"Value": 1, "Label": "File"}, {"Value": 2, "Label": "Folder"}], "display": "Item Type", "desc": "File or Folder"},
    {"name": "crad9_PrincipalName", "type": "StringAttributeMetadata", "maxLength": 255, "display": "Principal Name", "desc": "User or Group name"},
    {"name": "crad9_PrincipalType", "type": "PicklistAttributeMetadata", "options": [{"Value": 1, "Label": "User"}, {"Value": 2, "Label": "Group"}], "display": "Principal Type", "desc": "User or Group"},
    {"name": "crad9_PermissionLevel", "type": "StringAttributeMetadata", "maxLength": 500, "display": "Permission Level", "desc": "Combined permission levels"},
    {"name": "crad9_ScannedAt", "type": "DateTimeAttributeMetadata", "format": "DateAndTime", "behavior": 1, "display": "Scanned At", "desc": "When this permission was recorded"}
]

for col in perm_columns:
    col_def = {
        "@odata.type": f"Microsoft.Dynamics.CRM.{col['type']}",
        "AttributeType": col['type'].replace('AttributeMetadata', '').replace('Metadata', ''),
        "SchemaName": col['name'],
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": col['display'], "LanguageCode": 1033}]
        },
        "Description": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": col['desc'], "LanguageCode": 1033}]
        },
        "RequiredLevel": {"Value": "None"}
    }

    if col['type'] == 'StringAttributeMetadata':
        col_def["AttributeTypeName"] = {"Value": "StringType"}
        col_def["MaxLength"] = col['maxLength']
    elif col['type'] == 'DateTimeAttributeMetadata':
        col_def["Format"] = col['format']
        col_def["Behavior"] = col['behavior']
    elif col['type'] == 'PicklistAttributeMetadata':
        col_def["OptionSet"] = {
            "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
            "Options": [
                {
                    "Value": opt["Value"],
                    "Label": {
                        "@odata.type": "Microsoft.Dynamics.CRM.Label",
                        "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": opt["Label"], "LanguageCode": 1033}]
                    }
                } for opt in col['options']
            ],
            "IsGlobal": False,
            "OptionSetType": "Picklist"
        }

    col_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_itempermission')/Attributes"
    req_data = json.dumps(col_def).encode('utf-8')
    req = urllib.request.Request(col_url, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  ✓ {col['name']}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        if 'already exists' in err_body.lower():
            print(f"  ✓ {col['name']} (already exists)")
        else:
            print(f"  ✗ {col['name']}: {err_body[:200]}")

# Add Meeting and Scan lookups
print("\n✓ Adding lookup relationships...")

for lookup_name, target_entity in [("Meeting", "crad9_meeting"), ("Scan", "crad9_scan")]:
    lookup_rel = {
        "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
        "SchemaName": f"crad9_{lookup_name}_crad9_ItemPermission",
        "ReferencedEntity": target_entity,
        "ReferencingEntity": "crad9_itempermission",
        "Lookup": {
            "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
            "AttributeType": "Lookup",
            "AttributeTypeName": {"Value": "LookupType"},
            "SchemaName": f"crad9_{lookup_name}",
            "DisplayName": {
                "@odata.type": "Microsoft.Dynamics.CRM.Label",
                "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": lookup_name, "LanguageCode": 1033}]
            },
            "RequiredLevel": {"Value": "ApplicationRequired"}
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

    req_data = json.dumps(lookup_rel).encode('utf-8')
    req = urllib.request.Request(rel_url, data=req_data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  ✓ {lookup_name} relationship")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        if 'already exists' in err_body.lower():
            print(f"  ✓ {lookup_name} relationship (already exists)")
        else:
            print(f"  ⚠ {lookup_name} relationship: {err_body[:200]}")

# =============================================================================
# Publish customizations
# =============================================================================

print("\n✓ Publishing customizations...")
publish_url = f"{API_URL}/PublishAllXml"
req = urllib.request.Request(publish_url, data=b'{}', headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("✓ Customizations published")
except Exception as e:
    print(f"⚠ Publish warning: {e}")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 70)
print("  ✓ Tables Created Successfully!")
print("=" * 70)
print()
print("  Tables:")
print("    • crad9_scan - Tracks scan sessions")
print("    • crad9_itempermission - Stores item permissions")
print()
print("  Next: Create the Power Automate flow using these tables")
print()
