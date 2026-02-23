#!/usr/bin/env python3
"""
Fix Meeting Folder URLs - Decode URL-encoded paths
Updates crad9_folderurl to store decoded paths instead of URL-encoded paths
"""

import json
import urllib.request
import urllib.parse
import urllib.error

from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

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

# Get Dataverse token
DATAVERSE_TOKEN = get_token(f"{ORG_URL}/.default")

def get_all_meetings():
    """Fetch all meetings with folder URLs"""
    url = f"{API_URL}/crad9_meetings"
    params = urllib.parse.urlencode({
        "$select": "crad9_meetingid,crad9_newcolumn,crad9_folderurl",
        "$filter": "crad9_folderurl ne null"
    })

    req = urllib.request.Request(f"{url}?{params}")
    req.add_header('Authorization', f'Bearer {DATAVERSE_TOKEN}')
    req.add_header('Accept', 'application/json')
    req.add_header('OData-MaxVersion', '4.0')
    req.add_header('OData-Version', '4.0')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('value', [])
    except urllib.error.HTTPError as e:
        print(f"❌ Error fetching meetings: {e.code}")
        print(e.read().decode())
        return []

def decode_folder_url(encoded_url):
    """
    Decode URL-encoded folder URL

    Example:
    Input:  https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget%20Meeting-%20%5BUrgent%5D
    Output: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]
    """
    return urllib.parse.unquote(encoded_url)

def update_meeting_folder_url(meeting_id, decoded_url):
    """Update meeting record with decoded folder URL"""
    url = f"{API_URL}/crad9_meetings({meeting_id})"

    data = json.dumps({
        "crad9_folderurl": decoded_url
    }).encode()

    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('Authorization', f'Bearer {DATAVERSE_TOKEN}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    req.add_header('OData-MaxVersion', '4.0')
    req.add_header('OData-Version', '4.0')

    try:
        with urllib.request.urlopen(req) as response:
            return response.status == 204
    except urllib.error.HTTPError as e:
        print(f"      ❌ Update failed: {e.code}")
        return False

def main():
    print("=" * 80)
    print("🔧 FIXING FOLDER URLs - Decoding URL-encoded Paths")
    print("=" * 80)
    print()

    # Get all meetings
    print("📋 Fetching meetings from Dataverse...")
    meetings = get_all_meetings()
    print(f"   Found {len(meetings)} meetings with folder URLs")
    print()

    if not meetings:
        print("⚠️  No meetings found with folder URLs")
        return

    # Process each meeting
    updated_count = 0
    unchanged_count = 0

    print("🔄 Processing meetings...")
    print()

    for meeting in meetings:
        meeting_id = meeting['crad9_meetingid']
        meeting_name = meeting.get('crad9_newcolumn', 'Unknown')
        current_url = meeting['crad9_folderurl']

        # Decode the URL
        decoded_url = decode_folder_url(current_url)

        print(f"📊 Meeting: {meeting_name}")
        print(f"   Current URL : {current_url}")
        print(f"   Decoded URL : {decoded_url}")

        # Check if decoding actually changed anything
        if current_url == decoded_url:
            print(f"   ℹ️  URL already decoded - no change needed")
            unchanged_count += 1
        else:
            # Update the record
            if update_meeting_folder_url(meeting_id, decoded_url):
                print(f"   ✅ Updated successfully")
                updated_count += 1
            else:
                print(f"   ❌ Update failed")

        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total meetings processed: {len(meetings)}")
    print(f"✅ Updated with decoded URLs: {updated_count}")
    print(f"ℹ️  Already decoded (no change): {unchanged_count}")
    print()

    if updated_count > 0:
        print("✅ Folder URLs have been decoded!")
        print("   Your flow should now work correctly with FileRef filtering.")
    else:
        print("ℹ️  All folder URLs were already decoded.")

    print()
    print("🔍 Next Steps:")
    print("   1. Test your flow with one of the updated meetings")
    print("   2. Verify that Send_HTTP_to_SharePoint returns items")
    print("   3. Check that the filter startswith(FileRef,'...') works correctly")
    print()

if __name__ == "__main__":
    main()
