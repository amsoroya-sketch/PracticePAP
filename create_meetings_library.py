#!/usr/bin/env python3
"""
Create 'Meetings' document library in existing SharePoint site
Target: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test
"""

import json
import urllib.request
import urllib.parse
import sys

# =============================================================================
# Configuration
# =============================================================================
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"

SITE_URL = f"{SP_ROOT_URL}/sites/Permission-Scanner-Test"
SITE_ALIAS = "Permission-Scanner-Test"
LIBRARY_NAME = "Meetings"

# =============================================================================
# Get tokens
# =============================================================================

print("\n" + "=" * 60)
print("  Create 'Meetings' Library")
print(f"  Site: {SITE_URL}")
print("=" * 60)

def get_token(scope):
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': scope
    }).encode('utf-8')

    req = urllib.request.Request(token_url, data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8')).get('access_token')

print("\n✓ Authenticating...")
graph_token = get_token("https://graph.microsoft.com/.default")
sp_token = get_token(f"{SP_ROOT_URL}/.default") or graph_token

# =============================================================================
# Get site ID
# =============================================================================

print("✓ Getting site information...")
site_check_url = f"https://graph.microsoft.com/v1.0/sites/root:/sites/{SITE_ALIAS}"
req = urllib.request.Request(site_check_url, headers={'Authorization': f'Bearer {graph_token}'})

try:
    with urllib.request.urlopen(req) as resp:
        site_info = json.loads(resp.read().decode('utf-8'))
        site_id = site_info['id']
        print(f"  Site ID: {site_id}")
except Exception as e:
    print(f"✗ Error getting site: {e}")
    sys.exit(1)

# =============================================================================
# Check if library already exists
# =============================================================================

print(f"\n✓ Checking for existing '{LIBRARY_NAME}' library...")
drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
req = urllib.request.Request(drives_url, headers={'Authorization': f'Bearer {graph_token}'})

existing_drive = None
try:
    with urllib.request.urlopen(req) as resp:
        drives = json.loads(resp.read().decode('utf-8'))
        for drive in drives.get('value', []):
            if drive.get('name') == LIBRARY_NAME:
                existing_drive = drive
                break
except Exception as e:
    print(f"  Warning: Could not check existing libraries: {e}")

if existing_drive:
    print(f"\n{'='*60}")
    print(f"  ✓ Library '{LIBRARY_NAME}' already exists!")
    print(f"{'='*60}")
    print(f"  Drive ID: {existing_drive.get('id')}")
    print(f"  Web URL: {existing_drive.get('webUrl')}")
    print()
    sys.exit(0)

# =============================================================================
# Create library via SharePoint REST API
# =============================================================================

print(f"✓ Creating '{LIBRARY_NAME}' library...")

create_lib_url = f"{SITE_URL}/_api/web/lists"
lib_payload = {
    "__metadata": {"type": "SP.List"},
    "AllowContentTypes": True,
    "BaseTemplate": 101,  # Document Library
    "ContentTypesEnabled": True,
    "Description": "Meeting documents and agenda item folders",
    "Title": LIBRARY_NAME
}

headers = {
    'Authorization': f'Bearer {sp_token}',
    'Content-Type': 'application/json;odata=verbose',
    'Accept': 'application/json;odata=verbose'
}

req_data = json.dumps(lib_payload).encode('utf-8')
req = urllib.request.Request(create_lib_url, data=req_data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        create_resp = json.loads(resp.read().decode('utf-8'))
        lib_title = create_resp.get('d', {}).get('Title')
        if lib_title:
            print(f"\n{'='*60}")
            print(f"  ✓ Library '{lib_title}' created successfully!")
            print(f"{'='*60}")
        else:
            print("\n  Warning: Library creation response unclear")
            print(json.dumps(create_resp, indent=2))
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    print(f"\n✗ Error creating library (HTTP {e.code}):")
    try:
        err_json = json.loads(err_body)
        print(json.dumps(err_json, indent=2))
    except:
        print(err_body[:500])
    sys.exit(1)

# =============================================================================
# Verify creation
# =============================================================================

print("\n✓ Verifying library creation...")
import time
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL
time.sleep(3)

req = urllib.request.Request(drives_url, headers={'Authorization': f'Bearer {graph_token}'})
try:
    with urllib.request.urlopen(req) as resp:
        drives = json.loads(resp.read().decode('utf-8'))
        for drive in drives.get('value', []):
            if drive.get('name') == LIBRARY_NAME:
                print(f"\n{'='*60}")
                print(f"  ✓ Verification successful!")
                print(f"{'='*60}")
                print(f"  Library: {LIBRARY_NAME}")
                print(f"  Drive ID: {drive.get('id')}")
                print(f"  Web URL: {drive.get('webUrl')}")
                print(f"\n  Next steps:")
                print(f"    1. Import Power Automate flows (CreateMeetingSPFolder, CreateAgendaItemSPFolder)")
                print(f"    2. Create a test meeting with 'Is User Allowed SP Folder' = Yes")
                print(f"    3. Verify folder auto-creation in SharePoint")
                print()
                sys.exit(0)
except Exception as e:
    print(f"  Warning: Could not verify: {e}")

print()
