#!/usr/bin/env python3
"""
List existing SharePoint sites accessible with current credentials
"""

import json
import urllib.request
import urllib.parse
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# =============================================================================
# Configuration (from MSDev .env)
# =============================================================================
SP_ROOT_URL = "https://ABCTest179.sharepoint.com"

# =============================================================================
# Get access token
# =============================================================================

print("\nAuthenticating with Microsoft Graph API...")
token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
data = urllib.parse.urlencode({
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'scope': 'https://graph.microsoft.com/.default'
}).encode('utf-8')

req = urllib.request.Request(token_url, data=data)
with urllib.request.urlopen(req) as resp:
    token_resp = json.loads(resp.read().decode('utf-8'))
    token = token_resp['access_token']

print("✓ Token obtained\n")

# =============================================================================
# List SharePoint sites
# =============================================================================

print("=" * 70)
print("  Available SharePoint Sites")
print("=" * 70)

# Get all sites
sites_url = "https://graph.microsoft.com/v1.0/sites?search=*"
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

req = urllib.request.Request(sites_url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        sites_resp = json.loads(resp.read().decode('utf-8'))

        if 'value' in sites_resp:
            for i, site in enumerate(sites_resp['value'], 1):
                print(f"\n{i}. {site.get('displayName', 'N/A')}")
                print(f"   URL: {site.get('webUrl', 'N/A')}")
                print(f"   ID: {site.get('id', 'N/A')}")

                # Get document libraries for this site
                site_id = site.get('id')
                if site_id:
                    drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
                    req2 = urllib.request.Request(drives_url, headers=headers)
                    try:
                        with urllib.request.urlopen(req2) as resp2:
                            drives_resp = json.loads(resp2.read().decode('utf-8'))
                            if 'value' in drives_resp and drives_resp['value']:
                                print(f"   Libraries:")
                                for drive in drives_resp['value']:
                                    print(f"     - {drive.get('name', 'N/A')}")
                    except:
                        pass

            print(f"\n{'-' * 70}")
            print(f"Total sites found: {len(sites_resp['value'])}")
        else:
            print("No sites found or insufficient permissions")

except urllib.error.HTTPError as e:
    print(f"Error: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")

print()
