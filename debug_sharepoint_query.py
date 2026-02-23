#!/usr/bin/env python3
"""
Debug SharePoint Query - Check what's being returned
Tests the exact filter your flow is using
"""

import json
import urllib.request
import urllib.parse
import urllib.error

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
        return None

def get_meeting_by_name(meeting_name):
    """Get a specific meeting record"""
    token = get_token(f"{ORG_URL}/.default")
    if not token:
        return None

    url = f"{API_URL}/crad9_meetings"
    params = urllib.parse.urlencode({
        "$select": "crad9_meetingid,crad9_newcolumn,crad9_folderurl,crad9_level",
        "$filter": f"contains(crad9_newcolumn,'{meeting_name}')",
        "$top": "1"
    })

    req = urllib.request.Request(f"{url}?{params}")
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = data.get('value', [])
            return results[0] if results else None
    except urllib.error.HTTPError as e:
        print(f"❌ Error: {e.code} - {e.read().decode()}")
        return None

def parse_folder_url(folder_url):
    """Parse folder URL to extract site URL and folder path (mimics flow logic)"""
    parts = folder_url.split('/')

    # Site URL: parts[0] + '//' + parts[2] + '/sites/' + parts[4]
    site_url = f"{parts[0]}//{parts[2]}/sites/{parts[4]}"

    # Folder path: join parts from index 5 onwards
    folder_path = '/'.join(parts[5:])

    return site_url, folder_path

def test_sharepoint_query_no_filter():
    """Test 1: Get ALL items from Meetings library (no filter)"""
    print("=" * 80)
    print("🧪 TEST 1: Get ALL items from Meetings library (NO filter)")
    print("=" * 80)

    # This should work with user delegated permissions via browser
    # For now, just show what the query would be
    query = f"{SITE_URL}/_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType&$top=50"

    print(f"Query: {query}")
    print()
    print("⚠️  Note: This requires user authentication (not app-only token)")
    print("   You can test this in your browser while logged into SharePoint:")
    print(f"   1. Go to: {query}")
    print(f"   2. You should see JSON with all items")
    print()

def test_folder_path_logic(meeting_name):
    """Test 2: Check folder path extraction logic"""
    print("=" * 80)
    print(f"🧪 TEST 2: Folder Path Extraction for '{meeting_name}'")
    print("=" * 80)

    meeting = get_meeting_by_name(meeting_name)
    if not meeting:
        print(f"❌ Meeting not found: {meeting_name}")
        return None, None

    print(f"✅ Meeting found:")
    print(f"   Name: {meeting['crad9_newcolumn']}")
    print(f"   Folder URL: {meeting['crad9_folderurl']}")
    print(f"   Level: {meeting.get('crad9_level', 'Not set')}")
    print()

    site_url, folder_path = parse_folder_url(meeting['crad9_folderurl'])

    print(f"📊 Parsed Values (Flow Logic):")
    print(f"   Site URL: {site_url}")
    print(f"   Folder Path: {folder_path}")
    print()

    print(f"🔍 SharePoint Filter:")
    filter_expr = f"startswith(FileRef,'{folder_path}')"
    print(f"   Expression: {filter_expr}")
    print()

    print(f"📋 Full API URL:")
    full_url = f"{site_url}/_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter={filter_expr}&$top=500"
    print(f"   {full_url}")
    print()

    return site_url, folder_path

def test_with_power_automate():
    """Test 3: Instructions for Power Automate"""
    print("=" * 80)
    print("🧪 TEST 3: How to Debug in Power Automate")
    print("=" * 80)
    print()
    print("In your Power Automate flow:")
    print()
    print("1️⃣  After 'Set_Folder_Path' action, add a 'Compose' action:")
    print("   Name: Debug_Folder_Path")
    print("   Value: outputs('Set_Folder_Path')")
    print()
    print("2️⃣  After 'Send_HTTP_to_SharePoint' action, add a 'Compose' action:")
    print("   Name: Debug_HTTP_Response")
    print("   Value: body('Send_HTTP_to_SharePoint')")
    print()
    print("3️⃣  Run the flow and check the outputs:")
    print("   - Debug_Folder_Path should show: 'Meetings/Budget Meeting- [Urgent]'")
    print("   - Debug_HTTP_Response should show the JSON response")
    print()
    print("4️⃣  Common issues:")
    print("   ❌ If FileRef in response doesn't match your filter:")
    print("      → Items might be in a different path")
    print("      → Check actual FileRef values in the response")
    print()
    print("   ❌ If response has 0 items but folders exist:")
    print("      → Folders themselves aren't returned by default")
    print("      → Only FILES and SUBFOLDERS with content are returned")
    print("      → Empty folders = 0 items in response")
    print()

def main():
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SHAREPOINT QUERY DEBUGGER" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Test with Budget Meeting
    test_meeting = "Budget"

    test_folder_path_logic(test_meeting)

    print()
    test_sharepoint_query_no_filter()

    print()
    test_with_power_automate()

    print()
    print("=" * 80)
    print("💡 KEY INSIGHTS")
    print("=" * 80)
    print()
    print("1. Empty folders don't have items to return")
    print("   ✅ Solution: Add files or subfolders inside 'Budget Meeting- [Urgent]'")
    print()
    print("2. The filter matches the START of FileRef")
    print("   Example FileRef: 'Meetings/Budget Meeting- [Urgent]/Agenda.docx'")
    print("   Filter: startswith(FileRef,'Meetings/Budget Meeting- [Urgent]')")
    print("   ✅ This WILL match")
    print()
    print("3. Folder itself is not an item")
    print("   The folder 'Budget Meeting- [Urgent]' won't appear in results")
    print("   Only contents (files/subfolders) inside it will")
    print()
    print("=" * 80)
    print()
    print("🔍 NEXT STEP:")
    print(f"   Go to: {SITE_URL}/Meetings/Budget%20Meeting-%20%5BUrgent%5D")
    print("   Check if there are ANY files or folders inside")
    print("   If empty → Add at least 1 test file")
    print()

if __name__ == "__main__":
    main()
