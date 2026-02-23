#!/usr/bin/env python3
"""
Check Agenda Items in Dataverse
Verify if agenda items have SharePoint URLs
"""

import json
import urllib.request
import urllib.parse
import urllib.error

from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

def get_token():
    """Get OAuth access token"""
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': f"{ORG_URL}/.default"
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

def get_agenda_items():
    """Get all agenda items"""
    token = get_token()
    if not token:
        return []

    url = f"{API_URL}/crad9_agendaitems"
    params = urllib.parse.urlencode({
        "$select": "crad9_agendaitemid,crad9_name",
        "$expand": "crad9_Meeting($select=crad9_newcolumn)",
        "$top": "50"
    })

    req = urllib.request.Request(f"{url}?{params}")
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('value', [])
    except urllib.error.HTTPError as e:
        print(f"❌ Error: {e.code}")
        print(e.read().decode())
        return []

def main():
    print("=" * 80)
    print("📋 CHECKING AGENDA ITEMS IN DATAVERSE")
    print("=" * 80)
    print()

    items = get_agenda_items()

    print(f"Total agenda items found: {len(items)}")
    print()

    if not items:
        print("⚠️  No agenda items found in Dataverse")
        print()
        print("This means:")
        print("  - Agenda items haven't been created yet, OR")
        print("  - They exist but aren't linked to meetings")
        return

    with_url = []
    without_url = []

    print("📊 Agenda Items:")
    print()

    for item in items:
        name = item.get('crad9_name', 'Unnamed')
        meeting = item.get('crad9_Meeting', {})
        meeting_name = meeting.get('crad9_newcolumn', 'No meeting') if meeting else 'No meeting'

        print(f"  • {name}")
        print(f"    Meeting: {meeting_name}")
        print()

    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total agenda items found: {len(items)}")
    print()

    if items:
        print("✅ Agenda items exist in Dataverse!")
        print()
        print("⚠️  IMPORTANT:")
        print("   Agenda items in Dataverse ≠ Files in SharePoint")
        print()
        print("   For your Permission Scanner flow to find items:")
        print("   1. Files/folders must physically exist in SharePoint")
        print("   2. They must be inside the meeting folder path")
        print()
        print("   Next step:")
        print("   - Check SharePoint folder contents manually:")
        print("     https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget%20Meeting-%20%5BUrgent%5D")
        print("   - If empty → Upload test files or run CreateAgendaItemSPFile flow")

if __name__ == "__main__":
    main()
