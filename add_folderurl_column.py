#!/usr/bin/env python3
"""
Add crad9_folderurl column to crad9_meeting table
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
# Get access token
# =============================================================================

print("\n" + "=" * 60)
print("  Add folderURL column to crad9_meeting")
print("=" * 60)

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
    TOKEN = token_resp['access_token']

print("\n✓ Authentication successful")

# =============================================================================
# Check if column already exists
# =============================================================================

print("\n✓ Checking if crad9_folderurl already exists...")

check_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_meeting')/Attributes(LogicalName='crad9_folderurl')"
headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
    'OData-Version': '4.0'
}

req = urllib.request.Request(check_url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        existing = json.loads(resp.read().decode('utf-8'))
        print(f"\n✓ Column already exists: {existing.get('LogicalName')}")
        print(f"  Type: {existing.get('@odata.type', 'N/A').split('.')[-1]}")
        print(f"  Display Name: {existing.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
        print(f"  Max Length: {existing.get('MaxLength', 'N/A')}")
        print("\nNo changes needed.")
        sys.exit(0)
except urllib.error.HTTPError as e:
    if e.code == 404:
        print("  Column does not exist - proceeding with creation...")
    else:
        print(f"  Error checking: {e.code}")
        sys.exit(1)

# =============================================================================
# Create the column
# =============================================================================

print("\n✓ Creating crad9_folderurl column...")

create_url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_meeting')/Attributes"

column_def = {
    "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
    "AttributeType": "String",
    "AttributeTypeName": {
        "Value": "StringType"
    },
    "MaxLength": 500,
    "Format": "Url",
    "SchemaName": "crad9_FolderURL",
    "LogicalName": "crad9_folderurl",
    "DisplayName": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [
            {
                "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                "Label": "Folder URL",
                "LanguageCode": 1033
            }
        ]
    },
    "Description": {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [
            {
                "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                "Label": "SharePoint folder URL for this meeting",
                "LanguageCode": 1033
            }
        ]
    },
    "RequiredLevel": {
        "Value": "None",
        "CanBeChanged": True
    }
}

headers['Content-Type'] = 'application/json'
req_data = json.dumps(column_def).encode('utf-8')
req = urllib.request.Request(create_url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("\n✓ Column created successfully!")
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f"\n✗ Error creating column (HTTP {e.code}):")
    try:
        err_json = json.loads(err_body)
        print(json.dumps(err_json, indent=2))
    except:
        print(err_body[:500])
    sys.exit(1)

# =============================================================================
# Publish customizations
# =============================================================================

print("\n✓ Publishing customizations...")

publish_url = f"{API_URL}/PublishAllXml"
req = urllib.request.Request(publish_url, data=b'{}', headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        print("\n" + "=" * 60)
        print("  ✓ Column added successfully!")
        print("=" * 60)
        print(f"\n  crad9_meeting.crad9_folderurl")
        print(f"    Type: String (URL)")
        print(f"    Max Length: 500 characters")
        print(f"    Display Name: Folder URL")
        print(f"\n  This column will store the SharePoint folder URL")
        print(f"  populated by the CreateMeetingSPFolder workflow.")
        print()
except urllib.error.HTTPError as e:
    print(f"\n  Warning: Publish may have failed ({e.code})")
    print("  The column was created but may need manual publish.")

print()
