#!/usr/bin/env python3
"""
Create SharePoint Folders for Meetings
Creates actual folders in SharePoint Meetings library based on meeting records
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time

from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"
SITE_URL = f"{SP_ROOT_URL}/sites/Permission-Scanner-Test"

def get_token(scope):
    """Get OAuth access token"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': scope
    }).encode()

    req = urllib.request.Request(token_url, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['access_token']
    except urllib.error.HTTPError as e:
        print(f"❌ Token error: {e.code}")
        print(e.read().decode())
        return None

def get_all_meetings():
    """Fetch all meetings with folder URLs"""
    token = get_token(f"{ORG_URL}/.default")
    if not token:
        return []

    url = f"{API_URL}/crad9_meetings"
    params = urllib.parse.urlencode({
        "$select": "crad9_meetingid,crad9_newcolumn,crad9_folderurl",
        "$filter": "crad9_folderurl ne null"
    })

    req = urllib.request.Request(f"{url}?{params}")
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/json')
    req.add_header('OData-MaxVersion', '4.0')
    req.add_header('OData-Version', '4.0')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('value', [])
    except urllib.error.HTTPError as e:
        print(f"❌ Error fetching meetings: {e.code}")
        return []

def create_folder_in_sharepoint(folder_name):
    """
    Create a folder in SharePoint Meetings library using Graph API
    Uses /children endpoint to POST a new folder
    """
    # Get Graph token
    graph_token = get_token("https://graph.microsoft.com/.default")
    if not graph_token:
        return False

    # Graph API endpoint - POST to parent folder's children
    site_path = "ABCTest179.sharepoint.com:/sites/Permission-Scanner-Test"
    url = f"https://graph.microsoft.com/v1.0/sites/{site_path}/drive/root:/Meetings:/children"

    # Create folder metadata
    folder_data = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "fail"
    }

    data = json.dumps(folder_data).encode()

    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {graph_token}')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"      ✅ Folder created: {result.get('name')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        if e.code == 409 or "nameAlreadyExists" in error_body:
            print(f"      ℹ️  Folder already exists")
            return True  # Already exists is okay
        else:
            print(f"      ❌ Error {e.code}: {error_body}")
            return False

def update_meeting_sp_created_flag(meeting_id):
    """Update meeting record to mark SharePoint folder as created"""
    token = get_token(f"{ORG_URL}/.default")
    if not token:
        return False

    url = f"{API_URL}/crad9_meetings({meeting_id})"
    data = json.dumps({
        "crad9_spfoldercreated": True
    }).encode()

    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            return response.status == 204
    except urllib.error.HTTPError:
        return False

def extract_folder_name(folder_url):
    """Extract just the folder name from full URL"""
    # Example: https://...sharepoint.../Meetings/Budget Meeting- [Urgent]
    # Returns: Budget Meeting- [Urgent]
    parts = folder_url.split('/')
    return parts[-1] if parts else None

def main():
    print("=" * 80)
    print("📁 CREATING SHAREPOINT FOLDERS FOR MEETINGS")
    print("=" * 80)
    print()

    # Get all meetings
    print("📋 Fetching meetings from Dataverse...")
    meetings = get_all_meetings()
    print(f"   Found {len(meetings)} meetings with folder URLs")
    print()

    if not meetings:
        print("⚠️  No meetings found")
        return

    # Process each meeting
    created_count = 0
    existing_count = 0
    failed_count = 0

    print("🔄 Creating SharePoint folders...")
    print()

    for meeting in meetings:
        meeting_id = meeting['crad9_meetingid']
        meeting_name = meeting.get('crad9_newcolumn', 'Unknown')
        folder_url = meeting['crad9_folderurl']
        folder_name = extract_folder_name(folder_url)

        print(f"📊 Meeting: {meeting_name}")
        print(f"   Folder: {folder_name}")

        if not folder_name:
            print(f"   ❌ Could not extract folder name from URL")
            failed_count += 1
            print()
            continue

        # Create folder
        if create_folder_in_sharepoint(folder_name):
            # Update Dataverse flag
            if update_meeting_sp_created_flag(meeting_id):
                print(f"   ✅ Folder created and flag updated")
                created_count += 1
            else:
                print(f"   ⚠️  Folder created but flag update failed")
                created_count += 1
        else:
            print(f"   ❌ Failed to create folder")
            failed_count += 1

        print()
        time.sleep(0.5)  # Rate limiting

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total meetings processed: {len(meetings)}")
    print(f"✅ Folders created successfully: {created_count}")
    print(f"ℹ️  Folders already existed: {existing_count}")
    print(f"❌ Failed to create: {failed_count}")
    print()

    if created_count > 0:
        print("✅ SharePoint folders have been created!")
        print("   Your flow should now return items when scanning these folders.")
        print()
        print("🧪 Next Steps:")
        print("   1. Go to SharePoint: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings")
        print("   2. Verify folders exist")
        print("   3. Add some test files/folders inside each meeting folder")
        print("   4. Test your Power Automate flow")
    else:
        print("⚠️  No folders were created. Check the errors above.")

if __name__ == "__main__":
    main()
