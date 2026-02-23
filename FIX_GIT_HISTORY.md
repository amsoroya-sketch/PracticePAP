# Fix Git History - Remove Secrets

## 🚨 Problem

GitHub is blocking pushes because secrets exist in **previous commits** (not just the current one).

The secret is in commit: `51a5f3dd38d7176732a8a5301b2013615b3c821f`

---

## ✅ **SOLUTION: Rewrite Git History**

### **Option 1: Interactive Rebase (Recommended)**

```bash
# 1. Start interactive rebase from before the bad commit
git rebase -i d3468da  # (commit before "changes")

# 2. In the editor that opens, change "pick" to "edit" for commit 51a5f3d

# 3. When rebase stops at that commit, remove the secrets:
bash fix_all_secrets.sh

# 4. Stage the changes
git add .

# 5. Amend the commit
git commit --amend --no-edit

# 6. Continue rebase
git rebase --continue

# 7. Force push (DANGER: This rewrites history!)
git push --force-with-lease
```

---

### **Option 2: Reset and Recommit (Simpler)**

```bash
# 1. Create a backup branch
git branch backup-before-reset

# 2. Reset to the commit BEFORE secrets were added
git reset --soft d3468da  # Keeps all your changes staged

# 3. Unstage everything
git reset

# 4. Now stage only non-secret files
git add .gitignore config.py .env.example README_CREDENTIALS.md
git add *.md *.html *.sh

# 5. Stage Python files (now without secrets)
git add *.py

# 6. Commit
git commit -m "feat: add Power Automate flow documentation and scripts

- Add complete step-by-step flow build guide
- Add dynamic configuration extraction
- Add validation scripts
- Move credentials to .env file for security"

# 7. Force push
git push --force-with-lease
```

---

###  **Option 3: Fresh Start (Nuclear Option)**

If the repository doesn't have important history:

```bash
# 1. Remove git history
rm -rf .git

# 2. Initialize new repo
git init
git add .
git commit -m "Initial commit with secure credential handling"

# 3. Add remote
git remote add origin git@github.com:amsoroya-sketch/PracticePAP.git

# 4. Force push
git push -u origin main --force
```

---

## ⚠️ **CRITICAL: Before Force Pushing**

1. **Rotate the exposed secret immediately!**
   - Go to Azure Portal
   - Delete the exposed client secret
   - Create a NEW client secret
   - Update your `.env` file with the new secret

2. **Verify `.env` is NOT staged:**
   ```bash
   git status | grep .env  # Should show nothing
   ```

3. **Verify `.gitignore` exists:**
   ```bash
   cat .gitignore | grep .env  # Should show .env entries
   ```

---

## 🔐 **After Fixing Git History**

1. **Rotate the Azure AD client secret** (see above)

2. **Verify the fix worked:**
   ```bash
   # Check that secrets don't appear in history
   git log -p | grep "CLIENT_SECRET.*="
   # Should only show removals (lines starting with -)
   ```

3. **Push successfully:**
   ```bash
   git push
   ```

---

## 📝 **Recommended: Option 2 (Reset and Recommit)**

This is the safest for this situation because:
- ✅ Preserves all your code
- ✅ Simple to execute
- ✅ Creates clean history
- ✅ No complex rebase conflicts

---

**Next Steps:**

1. Choose an option above
2. Execute the commands
3. Verify secrets are gone: `git log -p | grep "CLIENT_SECRET"`
4. Push: `git push --force-with-lease`
5. **ROTATE THE SECRET in Azure Portal!**
