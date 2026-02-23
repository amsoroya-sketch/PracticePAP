#!/usr/bin/env python3
"""
Remove hardcoded secrets from Python files
Replaces hardcoded credentials with imports from config.py
"""

import re
import os
from pathlib import Path

def fix_file(filepath):
    """Remove hardcoded credentials from a Python file"""
    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # Pattern to match the hardcoded configuration section
    config_pattern = r'# Configuration\s*\nTENANT_ID\s*=\s*["\'].*?["\']\s*\nCLIENT_ID\s*=\s*["\'].*?["\']\s*\nCLIENT_SECRET\s*=\s*["\'].*?["\']\s*\nORG_URL\s*=\s*["\'].*?["\']\s*\nAPI_URL\s*=\s*f["\'].*?["\']'

    # Check if file has the hardcoded config
    if re.search(config_pattern, content):
        # Replace with import
        content = re.sub(
            config_pattern,
            'from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL',
            content
        )

        # Check if we successfully replaced
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed: {filepath}")
            return True
        else:
            print(f"⚠️  Pattern not matched in: {filepath}")
            return False
    else:
        print(f"ℹ️  No hardcoded config found in: {filepath}")
        return False

def main():
    print("=" * 80)
    print("🔒 REMOVING HARDCODED SECRETS FROM PYTHON FILES")
    print("=" * 80)
    print()

    # Get all Python files in current directory
    py_files = [f for f in Path('.').glob('*.py') if f.name != 'config.py' and f.name != 'remove_secrets_from_files.py']

    fixed_count = 0
    for py_file in py_files:
        if fix_file(py_file):
            fixed_count += 1

    print()
    print("=" * 80)
    print(f"✅ Fixed {fixed_count} files")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review the changes with: git diff")
    print("2. Test a script to ensure it still works")
    print("3. Commit changes: git add . && git commit -m 'refactor: move credentials to .env file'")
    print("4. Push to GitHub: git push")
    print()

if __name__ == "__main__":
    main()
