#!/usr/bin/env python3
"""
SharePoint Site Provisioner - Meeting Management

Creates a new SharePoint site and Meetings document library using
Microsoft Graph API with existing app registration credentials.

Site:    https://ABCTest179.sharepoint.com/sites/MeetingManagement
Library: Meetings
Folder structure: /Meetings/{MeetingName}/{AgendaItemName}/
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
import sys
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration (from MSDev .env)
# =============================================================================
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"

NEW_SITE_ALIAS = "MeetingManagement"
NEW_SITE_TITLE = "Meeting Management"
NEW_SITE_URL = f"{SP_ROOT_URL}/sites/{NEW_SITE_ALIAS}"
LIBRARY_NAME = "Meetings"

# =============================================================================
# Utility functions
# =============================================================================

def log(msg):
    print(f"\033[0;34m[INFO]\033[0m  {msg}")

def ok(msg):
    print(f"\033[0;32m[OK]\033[0m    {msg}")

def warn(msg):
    print(f"\033[1;33m[WARN]\033[0m  {msg}")

def error(msg):
    print(f"\033[0;31m[ERROR]\033[0m {msg}")
    sys.exit(1)

def api_call(method, url, data=None, headers=None, parse_json=True):
    """Make an HTTP request and return parsed JSON or raw response"""
    if headers is None:
        headers = {}

    req_data = None
    if data:
        req_data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            return json.loads(body) if parse_json and body else body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        if parse_json:
            try:
                return json.loads(err_body)
            except:
                pass
        warn(f"HTTP {e.code}: {err_body[:500]}")
        return None
    except Exception as e:
        warn(f"Request failed: {e}")
        return None

def get_token(scope):
    """Get OAuth2 access token for specified scope"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': scope
    }

    encoded_data = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(token_url, data=encoded_data)

    try:
        with urllib.request.urlopen(req) as resp:
            token_resp = json.loads(resp.read().decode('utf-8'))
            return token_resp.get('access_token')
    except Exception as e:
        error(f"Failed to get access token: {e}")

# =============================================================================
# Main Provisioning Flow
# =============================================================================

print("")
print("=" * 50)
print("  SharePoint Site Provisioner")
print(f"  Target: {NEW_SITE_URL}")
print("=" * 50)
print("")

# Step 1: Get Graph API token
log("Authenticating with Microsoft Graph API...")
graph_token = get_token("https://graph.microsoft.com/.default")
if not graph_token:
    error("Failed to obtain Graph API access token")
ok("Graph API token obtained")

# Step 2: Check if site already exists
log(f"Checking if site '{NEW_SITE_ALIAS}' already exists...")
site_check_url = f"https://graph.microsoft.com/v1.0/sites/root:/sites/{NEW_SITE_ALIAS}"
site_check = api_call("GET", site_check_url, headers={'Authorization': f'Bearer {graph_token}'})

site_id = None
if site_check and 'id' in site_check:
    site_id = site_check['id']
    warn(f"Site already exists: {NEW_SITE_URL}")
    warn(f"Site ID: {site_id}")
else:
    # Step 3: Create site via SharePoint REST API
    log(f"Creating SharePoint site: {NEW_SITE_URL} ...")

    # Get SharePoint-specific token
    sp_token = get_token(f"{SP_ROOT_URL}/.default")
    if not sp_token:
        warn("Could not get SharePoint token - trying Graph token...")
        sp_token = graph_token

    create_site_url = f"{SP_ROOT_URL}/_api/SPSiteManager/create"
    site_payload = {
        "request": {
            "Title": NEW_SITE_TITLE,
            "Url": NEW_SITE_URL,
            "Lcid": 1033,
            "ShareByEmailEnabled": False,
            "Description": "Meeting Management - document repository for meeting agenda items",
            "WebTemplate": "STS#3",
            "SiteDesignId": "00000000-0000-0000-0000-000000000000",
            "Owner": CLIENT_ID
        }
    }

    headers = {
        'Authorization': f'Bearer {sp_token}',
        'Content-Type': 'application/json;odata.metadata=none',
        'Accept': 'application/json;odata.metadata=none'
    }

    create_resp = api_call("POST", create_site_url, data=site_payload, headers=headers)

    if create_resp and (create_resp.get('SiteStatus') == '2' or create_resp.get('SiteUrl')):
        ok(f"Site created: {create_resp.get('SiteUrl', NEW_SITE_URL)}")
    else:
        warn("Site creation response:")
        if create_resp:
            print(json.dumps(create_resp, indent=2))
        warn("Site may already exist or creation may be processing...")
        warn(f"Check: {NEW_SITE_URL}")

    # Wait for provisioning
    log("Waiting 15 seconds for site to provision...")
    time.sleep(15)

    # Re-fetch site ID
    site_check = api_call("GET", site_check_url, headers={'Authorization': f'Bearer {graph_token}'})
    if site_check and 'id' in site_check:
        site_id = site_check['id']

if not site_id:
    warn("Could not confirm site ID. Attempting to continue with known URL...")
    site_id = f"root:/sites/{NEW_SITE_ALIAS}"

ok(f"Site ID: {site_id}")

# Step 4: Create 'Meetings' document library
log(f"Creating '{LIBRARY_NAME}' document library...")

# Get existing drives (libraries)
drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
drives = api_call("GET", drives_url, headers={'Authorization': f'Bearer {graph_token}'})

existing_drive = None
if drives and 'value' in drives:
    for drive in drives['value']:
        if drive.get('name') == LIBRARY_NAME:
            existing_drive = drive.get('id')
            break

if existing_drive:
    warn(f"'{LIBRARY_NAME}' library already exists (Drive ID: {existing_drive})")
    drive_id = existing_drive
else:
    # Create library via SharePoint REST
    sp_token2 = get_token(f"{SP_ROOT_URL}/.default")
    if not sp_token2:
        sp_token2 = graph_token

    create_lib_url = f"{NEW_SITE_URL}/_api/web/lists"
    lib_payload = {
        "__metadata": {"type": "SP.List"},
        "AllowContentTypes": True,
        "BaseTemplate": 101,
        "ContentTypesEnabled": True,
        "Description": "Meeting documents and agenda folders",
        "Title": LIBRARY_NAME
    }

    headers = {
        'Authorization': f'Bearer {sp_token2}',
        'Content-Type': 'application/json;odata=verbose',
        'Accept': 'application/json;odata=verbose'
    }

    create_lib = api_call("POST", create_lib_url, data=lib_payload, headers=headers)

    if create_lib and create_lib.get('d', {}).get('Title'):
        ok(f"Library '{create_lib['d']['Title']}' created")
    else:
        warn("Library creation response:")
        if create_lib:
            print(json.dumps(create_lib, indent=2))
        warn("Library may already exist or permissions may be needed.")

    # Re-fetch drive ID
    drives2 = api_call("GET", drives_url, headers={'Authorization': f'Bearer {graph_token}'})
    drive_id = None
    if drives2 and 'value' in drives2:
        for drive in drives2['value']:
            if drive.get('name') == LIBRARY_NAME:
                drive_id = drive.get('id')
                break

ok(f"Library drive ID: {drive_id if drive_id else 'not yet available'}")

# Summary
print("")
print("=" * 50)
print("\033[0;32m  SharePoint Provisioning Complete!\033[0m")
print("=" * 50)
print("")
print(f"  Site URL    : {NEW_SITE_URL}")
print(f"  Library     : {LIBRARY_NAME}")
print(f"  Folder path : /sites/MeetingManagement/Meetings/{{MeetingName}}/{{AgendaItemName}}")
print("")
print("  Expected folder structure:")
print("    Meetings/")
print("    ├── Board Meeting 2026-02/")
print("    │   ├── Agenda Item 1 - Budget Review/")
print("    │   ├── Agenda Item 2 - Quarterly Report/")
print("    │   └── Agenda Item 3 - HR Update/")
print("    └── Team Sync 2026-03/")
print("        ├── Agenda Item 1 - Project Status/")
print("        └── Agenda Item 2 - Risks/")
print("")
print("  Power Automate flows will auto-create these folders")
print("  when meetings are created in Dataverse.")
print("")
