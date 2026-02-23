#!/bin/bash
# Remove hardcoded secrets from all Python files

echo "🔒 Removing hardcoded secrets from Python files..."
echo ""

for file in *.py; do
    # Skip config.py and the cleanup scripts
    if [[ "$file" == "config.py" ]] || [[ "$file" == "remove_secrets_from_files.py" ]] || [[ "$file" == "fix_all_secrets.sh" ]]; then
        continue
    fi

    # Check if file contains the secret pattern
    if grep -q "CLIENT_SECRET.*=.*\"" "$file"; then
        echo "Processing: $file"

        # Remove the hardcoded config lines
        sed -i '/^TENANT_ID = "/d' "$file"
        sed -i '/^CLIENT_ID = "/d' "$file"
        sed -i '/^CLIENT_SECRET = "/d' "$file"
        sed -i '/^ORG_URL = "/d' "$file"
        sed -i '/^API_URL = f"/d' "$file"

        # Add the import if not already present
        if ! grep -q "from config import" "$file"; then
            # Find line number of last import statement
            last_import=$(grep -n "^import\|^from" "$file" | tail -1 | cut -d: -f1)

            if [ -n "$last_import" ]; then
                sed -i "${last_import}a from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL" "$file"
                echo "  ✅ Fixed $file"
            else
                echo "  ⚠️  Could not find imports in $file"
            fi
        else
            echo "  ℹ️  Already using config import"
        fi
    fi
done

echo ""
echo "✅ Done! All secrets removed."
echo ""
echo "Next steps:"
echo "  1. Test a script: python3 validate_folder_url_patterns.py"
echo "  2. Review changes: git diff"
echo "  3. Stage changes: git add ."
echo "  4. Commit: git commit -m 'refactor: move credentials to .env file'"
echo "  5. Push: git push"
