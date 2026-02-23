#!/usr/bin/env python3
"""
Validate Folder URL Patterns
Analyzes all meeting folder URLs to determine if simple dynamic expressions are safe
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

def get_all_meetings():
    """Get all meetings with folder URLs"""
    token = get_token()
    if not token:
        return []

    url = f"{API_URL}/crad9_meetings"
    params = urllib.parse.urlencode({
        "$select": "crad9_meetingid,crad9_newcolumn,crad9_folderurl",
        "$filter": "crad9_folderurl ne null",
        "$top": "100"
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

def analyze_url(url):
    """Analyze a single folder URL and categorize it"""
    if not url:
        return 'null_or_empty'

    parts = url.split('/')

    # Check basic structure
    if len(parts) < 6:
        return 'too_short'

    # Check if it's a standard team site
    if parts[3] == 'sites':
        if len(parts) == 7:
            # Standard: https://tenant.sharepoint.com/sites/site/library/folder
            return 'standard_team_site'
        elif len(parts) > 7:
            # Subsite: https://tenant.sharepoint.com/sites/site/subsite/library/folder
            return 'subsite'
        else:
            return 'sites_but_short'

    # Check if it's OneDrive
    elif parts[3] == 'personal':
        return 'personal_onedrive'

    # Check if it's root collection (no /sites/)
    elif len(parts) < 6 or 'sites' not in url:
        return 'root_collection'

    else:
        return 'unknown_pattern'

def check_encoding(url):
    """Check if URL has encoded characters"""
    return '%' in url

def extract_with_simple_expression(url):
    """Simulate what the simple expression would extract"""
    if not url:
        return None, None

    parts = url.split('/')

    try:
        list_title = parts[5] if len(parts) > 5 else None
        site_path = f"/{parts[3]}/{parts[4]}" if len(parts) > 4 else None
        return list_title, site_path
    except IndexError:
        return None, None

def main():
    print("=" * 80)
    print("🔍 FOLDER URL PATTERN VALIDATION")
    print("=" * 80)
    print()

    meetings = get_all_meetings()

    if not meetings:
        print("⚠️  No meetings with folder URLs found")
        return

    print(f"📊 Analyzing {len(meetings)} meetings with folder URLs...")
    print()

    # Pattern categorization
    patterns = {
        'standard_team_site': [],
        'subsite': [],
        'personal_onedrive': [],
        'root_collection': [],
        'too_short': [],
        'null_or_empty': [],
        'unknown_pattern': []
    }

    encoded_urls = []
    extraction_issues = []

    # Analyze each meeting
    for meeting in meetings:
        name = meeting.get('crad9_newcolumn', 'Unnamed')
        url = meeting.get('crad9_folderurl', '')

        # Categorize pattern
        pattern = analyze_url(url)
        patterns[pattern].append({
            'name': name,
            'url': url
        })

        # Check encoding
        if check_encoding(url):
            encoded_urls.append({
                'name': name,
                'url': url
            })

        # Test simple expression
        list_title, site_path = extract_with_simple_expression(url)

        # Validate extraction
        if url and pattern == 'standard_team_site':
            # For standard sites, check if extraction makes sense
            if not list_title or not site_path:
                extraction_issues.append({
                    'name': name,
                    'url': url,
                    'list_title': list_title,
                    'site_path': site_path,
                    'issue': 'Extraction returned None'
                })

    # Print Results
    print("=" * 80)
    print("📊 PATTERN ANALYSIS RESULTS")
    print("=" * 80)
    print()

    total = len(meetings)

    for pattern, items in patterns.items():
        count = len(items)
        percentage = (count / total * 100) if total > 0 else 0

        icon = "✅" if pattern == 'standard_team_site' else "⚠️"
        print(f"{icon} {pattern.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")

        # Show sample URLs
        if items and count <= 3:
            for item in items:
                print(f"     • {item['name']}")
                print(f"       {item['url'][:80]}...")
        elif items:
            print(f"     • Showing first 2 of {count}:")
            for item in items[:2]:
                print(f"       {item['name']}: {item['url'][:60]}...")

    print()

    # Encoding check
    if encoded_urls:
        print("⚠️  URL ENCODING DETECTED:")
        print(f"   {len(encoded_urls)} URLs contain encoded characters (%, e.g., %20 for space)")
        print("   These need uriComponentToString() in expression!")
        print()
        for item in encoded_urls[:3]:
            print(f"     • {item['name']}")
            print(f"       {item['url']}")
        print()

    # Extraction issues
    if extraction_issues:
        print("❌ EXTRACTION ISSUES:")
        print(f"   {len(extraction_issues)} URLs would fail with simple expression")
        print()
        for item in extraction_issues[:3]:
            print(f"     • {item['name']}")
            print(f"       URL: {item['url']}")
            print(f"       List Title: {item['list_title']}")
            print(f"       Site Path: {item['site_path']}")
        print()

    # Sample extraction test
    if patterns['standard_team_site']:
        print("=" * 80)
        print("🧪 SAMPLE EXTRACTION TEST (Standard Team Site)")
        print("=" * 80)
        print()

        sample = patterns['standard_team_site'][0]
        url = sample['url']
        parts = url.split('/')

        print(f"Meeting: {sample['name']}")
        print(f"URL: {url}")
        print()
        print("After split('/'):")
        for i, part in enumerate(parts):
            print(f"  [{i}] = '{part}'")
        print()

        list_title, site_path = extract_with_simple_expression(url)
        print("Simple Expression Results:")
        print(f"  Action 7a (List Title): '{list_title}'")
        print(f"  Action 7b (Site Path): '{site_path}'")
        print()

        # Decode if needed
        if '%' in list_title:
            decoded = urllib.parse.unquote(list_title)
            print(f"  ⚠️  Decoded List Title: '{decoded}'")
            print(f"  ⚠️  You MUST use uriComponentToString() in Action 7a!")
            print()

    # Recommendation
    print("=" * 80)
    print("🎯 RECOMMENDATION")
    print("=" * 80)
    print()

    standard_count = len(patterns['standard_team_site'])
    issue_count = sum(len(patterns[p]) for p in patterns if p != 'standard_team_site' and patterns[p])

    if standard_count == total:
        print("✅ ALL URLs are Standard Team Sites!")
        print()
        if encoded_urls:
            print("⚠️  However, URL encoding detected.")
            print()
            print("USE THIS EXPRESSION for Action 7a:")
            print("─" * 80)
            print("uriComponentToString(outputs('Parse_Folder_URL')[5])")
            print("─" * 80)
            print()
            print("USE THIS EXPRESSION for Action 7b:")
            print("─" * 80)
            print("concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])")
            print("─" * 80)
        else:
            print("✅ No encoding issues detected.")
            print()
            print("SIMPLE EXPRESSIONS ARE SAFE:")
            print("─" * 80)
            print("Action 7a: outputs('Parse_Folder_URL')[5]")
            print("Action 7b: concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])")
            print("─" * 80)
    else:
        print(f"⚠️  MIXED URL PATTERNS DETECTED!")
        print(f"   Standard Team Sites: {standard_count}")
        print(f"   Other Patterns: {issue_count}")
        print()
        print("USE SAFE EXPRESSIONS WITH VALIDATION:")
        print("─" * 80)
        print("Action 7a:")
        print("if(")
        print("  greaterOrEquals(length(outputs('Parse_Folder_URL')), 6),")
        print("  uriComponentToString(outputs('Parse_Folder_URL')[5]),")
        print("  'Meetings'")
        print(")")
        print()
        print("Action 7b:")
        print("if(")
        print("  and(")
        print("    greaterOrEquals(length(outputs('Parse_Folder_URL')), 5),")
        print("    equals(outputs('Parse_Folder_URL')[3], 'sites')")
        print("  ),")
        print("  concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4]),")
        print("  '/sites/Permission-Scanner-Test'")
        print(")")
        print("─" * 80)

    print()
    print("📖 See EXPRESSION_VALIDATION_ANALYSIS.md for detailed explanation")
    print()

if __name__ == "__main__":
    main()
