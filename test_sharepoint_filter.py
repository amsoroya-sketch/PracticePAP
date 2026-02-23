#!/usr/bin/env python3
"""
Test SharePoint Filter with Decoded Folder Path
Verifies that the decoded folder URL now returns items
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# Configuration
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"

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

def test_sharepoint_filter(folder_path):
    """Test SharePoint REST API with folder path filter"""

    # Get SharePoint token
    sp_token = get_token(f"{SP_ROOT_URL}/.default")
    if not sp_token:
        return None

    # Build API URL
    site_url = f"{SP_ROOT_URL}/sites/Permission-Scanner-Test"
    api_url = f"{site_url}/_api/web/lists/GetByTitle('Meetings')/items"

    # Build query parameters
    params = {
        "$select": "Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments",
        "$filter": f"startswith(FileRef,'{folder_path}')",
        "$top": "500"
    }

    query_string = urllib.parse.urlencode(params)
    full_url = f"{api_url}?{query_string}"

    print(f"🔍 Testing SharePoint API...")
    print(f"   Site: {site_url}")
    print(f"   Folder: {folder_path}")
    print(f"   API URL: {full_url}")
    print()

    req = urllib.request.Request(full_url)
    req.add_header('Authorization', f'Bearer {sp_token}')
    req.add_header('Accept', 'application/json;odata=verbose')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data.get('d', {}).get('results', [])

            print(f"✅ API Request Successful!")
            print(f"   Items found: {len(items)}")
            print()

            if items:
                print("📋 Items in folder:")
                for item in items:
                    item_type = "📁 Folder" if item.get('FSObjType') == 1 else "📄 File"
                    has_unique = "🔒 Unique permissions" if item.get('HasUniqueRoleAssignments') else "🔓 Inherited"
                    print(f"   {item_type} {item.get('FileLeafRef')} - {has_unique}")
                    print(f"      FileRef: {item.get('FileRef')}")
            else:
                print("⚠️  No items found in this folder")

            return items

    except urllib.error.HTTPError as e:
        print(f"❌ API Error: {e.code}")
        print(f"   {e.read().decode()}")
        return None

def main():
    print("=" * 80)
    print("🧪 TESTING SHAREPOINT FILTER WITH DECODED PATHS")
    print("=" * 80)
    print()

    # Test cases with decoded paths
    test_cases = [
        "Meetings/Budget Meeting- [Urgent]",
        "Meetings/Team Sync- Planning & Strategy",
        "Meetings/Project Review (2026-Q2)",
        "Meetings/Board Meeting Q1-2026",
        "Meetings/Dev Team-Backend-API Review"
    ]

    results = []

    for folder_path in test_cases:
        items = test_sharepoint_filter(folder_path)
        results.append({
            'folder': folder_path,
            'count': len(items) if items else 0,
            'success': items is not None
        })
        print()
        print("-" * 80)
        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)

    for result in results:
        status = "✅" if result['success'] and result['count'] > 0 else "⚠️" if result['success'] else "❌"
        print(f"{status} {result['folder']}: {result['count']} items")

    print()

    successful = sum(1 for r in results if r['success'] and r['count'] > 0)
    print(f"Total folders tested: {len(results)}")
    print(f"Successful queries: {successful}")
    print()

    if successful == len(results):
        print("✅ All SharePoint filters are working correctly!")
        print("   Your Power Automate flow should now return items.")
    else:
        print("⚠️  Some folders returned no items - they may be empty or not exist in SharePoint")

if __name__ == "__main__":
    main()
