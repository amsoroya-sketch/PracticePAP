# Flow Configuration Variables - Adding Compose Actions

## 🎯 Purpose

Remove hardcoded values from the Permission Scanner flow by adding two new Compose actions for configuration values:
1. **SharePoint List Title** (currently hardcoded as 'Meetings')
2. **Site Path Prefix** (currently hardcoded as '/sites/Permission-Scanner-Test')

## 📋 Changes Overview

### **New Actions Added**

| Action # | Name | Location | Purpose |
|----------|------|----------|---------|
| **7a** | `Config_List_Title` | After Action 7 (Set_Folder_Path) | Store SharePoint list title ("Meetings") |
| **7b** | `Config_Site_Path_Prefix` | After Action 7a | Store site path prefix ("/sites/Permission-Scanner-Test") |

### **Actions Modified**

| Action # | Name | What Changed |
|----------|------|--------------|
| **12** | `Send_HTTP_to_SharePoint` | Uri now references both new Compose actions |
| **19** | `Get_Item_Permissions` | Uri now references Config_List_Title |

---

## 📝 Detailed Instructions

### **NEW ACTION 7a: Config_List_Title**

**Add After:** Action 7 (Set_Folder_Path)

**Steps:**
1. Click **+ New step**
2. Search for: `compose`
3. Select **Compose** (Data Operations)

**Configuration:**

| Field | Value |
|-------|-------|
| **Inputs** | Type directly: `Meetings` |

**Rename to:** `Config_List_Title`

**💡 Why:** This is the SharePoint library name where meeting folders are stored. Making it a variable allows you to:
- Change the library name in one place
- Reuse the flow for different libraries
- Make the flow more readable

---

### **NEW ACTION 7b: Config_Site_Path_Prefix**

**Add After:** Action 7a (Config_List_Title)

**Steps:**
1. Click **+ New step**
2. Search for: `compose`
3. Select **Compose**

**Configuration:**

| Field | Value |
|-------|-------|
| **Inputs** | Type directly: `/sites/Permission-Scanner-Test` |

**Rename to:** `Config_Site_Path_Prefix`

**💡 Why:** SharePoint FileRef fields store server-relative paths starting with `/sites/[site-name]`. This prefix is critical for the filter to work correctly.

**⚠️ IMPORTANT:**
- Must start with `/sites/`
- Must NOT have trailing slash
- Must match your SharePoint site URL

**Example Values:**
- `/sites/Permission-Scanner-Test` ✅ Correct
- `/sites/MyCompanySite` ✅ Correct
- `sites/Permission-Scanner-Test` ❌ Missing leading slash
- `/sites/Permission-Scanner-Test/` ❌ Has trailing slash

---

## 🔧 Updated Action Configurations

### **UPDATED ACTION 12: Send_HTTP_to_SharePoint**

**Before (hardcoded values):**
```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/@{outputs('Set_Folder_Path')}')&$top=500
```

**After (using Compose variables):**
```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'@{outputs('Config_Site_Path_Prefix')}/@{outputs('Set_Folder_Path')}')&$top=500
```

**How to Update:**
1. Open Action 12: `Send_HTTP_to_SharePoint`
2. Click in the **Uri** field
3. Clear the existing value
4. Type (or paste) the new Uri directly in the field
5. Power Automate will automatically parse the `@{...}` sections as dynamic content

**What Changed:**
- `'Meetings'` → `'@{outputs('Config_List_Title')}'`
- `'/sites/Permission-Scanner-Test/` → `'@{outputs('Config_Site_Path_Prefix')}/`

---

### **UPDATED ACTION 19: Get_Item_Permissions**

**Before:**
```
_api/web/lists/GetByTitle('Meetings')/items(@{items('Apply_to_each_Item')?['Id']})/RoleAssignments?$expand=RoleDefinitionBindings,Member
```

**After:**
```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items(@{items('Apply_to_each_Item')?['Id']})/RoleAssignments?$expand=RoleDefinitionBindings,Member
```

**How to Update:**
1. Open Action 19: `Get_Item_Permissions`
2. Click in the **Uri** field
3. Clear the existing value
4. Type (or paste) the new Uri directly
5. Power Automate will parse `@{...}` automatically

**What Changed:**
- `'Meetings'` → `'@{outputs('Config_List_Title')}'`

---

## 🧪 Alternative: Using Concat Expression (Advanced)

If you prefer to use concat() in the Expression tab instead of direct entry, here are the updated expressions:

### **Action 12 Uri (Concat Version):**

```javascript
concat('_api/web/lists/GetByTitle(''',outputs('Config_List_Title'),''')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''',outputs('Config_Site_Path_Prefix'),'/',outputs('Set_Folder_Path'),''')&$top=500')
```

**How to use:**
1. Click in Uri field
2. Switch to **Expression** tab
3. Paste the expression above
4. Click **OK**

### **Action 19 Uri (Concat Version):**

```javascript
concat('_api/web/lists/GetByTitle(''',outputs('Config_List_Title'),''')/items(',items('Apply_to_each_Item')?['Id'],')/RoleAssignments?$expand=RoleDefinitionBindings,Member')
```

---

## 📊 Before vs After Comparison

### **Hardcoded Values (Before):**

| Location | Hardcoded Value | Issue |
|----------|-----------------|-------|
| Action 12 | `'Meetings'` | Must edit action to change library |
| Action 12 | `'/sites/Permission-Scanner-Test'` | Must edit action to change site |
| Action 19 | `'Meetings'` | Duplicate hardcoded value |

**Problems:**
- ❌ Changes require editing multiple actions
- ❌ Risk of typos when updating
- ❌ Difficult to reuse flow for different sites
- ❌ Not clear what values need to change for deployment

### **Configuration Variables (After):**

| Location | Variable | Value Set In |
|----------|----------|--------------|
| Action 12 | `@{outputs('Config_List_Title')}` | Action 7a |
| Action 12 | `@{outputs('Config_Site_Path_Prefix')}` | Action 7b |
| Action 19 | `@{outputs('Config_List_Title')}` | Action 7a |

**Benefits:**
- ✅ Single source of truth for each value
- ✅ Change once, updates everywhere
- ✅ Clear configuration section at top of flow
- ✅ Easy to deploy to different environments
- ✅ Self-documenting (variable names explain purpose)

---

## 🚀 Deployment to Different Environments

When deploying this flow to a different SharePoint site:

**Old Approach (Hardcoded):**
1. Export flow
2. Import to new environment
3. Find Action 12, update Uri
4. Find Action 19, update Uri
5. Test and hope you didn't miss anything

**New Approach (Variables):**
1. Export flow
2. Import to new environment
3. Update Action 7a: Change `Meetings` to new library name
4. Update Action 7b: Change `/sites/Permission-Scanner-Test` to new site path
5. Done! All actions automatically use new values

---

## ✅ Testing Checklist

After making these changes, test the flow:

- [ ] Action 7a shows value: `Meetings`
- [ ] Action 7b shows value: `/sites/Permission-Scanner-Test`
- [ ] Action 12 Uri displays with dynamic content chips (purple pills)
- [ ] Action 19 Uri displays with dynamic content chips
- [ ] Run flow with a test meeting
- [ ] Verify Action 12 returns SharePoint items (not empty array)
- [ ] Verify permissions are scanned correctly
- [ ] Check scan record shows correct counts

---

## 📋 Updated Action Order

For reference, here's the complete flow structure with new actions:

```
1. Try_Scope
2. Get_Meeting_Record
3. Condition_Check_FolderURL
   ├─ If yes:
   │  4. Create_Scan_Record
   │  5. Parse_Folder_URL
   │  6. Set_Site_URL
   │  7. Set_Folder_Path
   │  7a. Config_List_Title ⭐ NEW
   │  7b. Config_Site_Path_Prefix ⭐ NEW
   │  8. Initialize_Items_Array
   │  9. Initialize_Counter
   │  10. Initialize_Permissions_Counter
   │  11. Initialize_Broken_Counter
   │  12. Send_HTTP_to_SharePoint (MODIFIED) ⭐
   │  13. Parse_Items_Response
   │  14. Filter_Broken_Permissions
   │  15. Filter_By_Level
   │  16. Apply_to_each_Item
   │      17. Condition_Not_Null
   │          18. Increment_Broken_Counter
   │          19. Get_Item_Permissions (MODIFIED) ⭐
   │          20. Parse_Permissions
   │          21. Apply_to_each_Permission
   │              22. Select_Permission_Names
   │              23. Join_Permissions
   │              24. Create_Permission_Record
   │              25. Increment_Permissions_Counter
   │          26. Increment_Items_Counter
   │  27. Update_Scan_Complete
   └─ If no:
      28. Terminate_No_FolderURL
29. Update_Scan_Failed (Catch)
```

---

## 💡 Future Enhancements

With this pattern established, you can add more configuration variables:

**Suggested Future Variables:**
- `Config_Max_Items` (currently hardcoded as `500` in `$top=500`)
- `Config_Select_Fields` (the field list in `$select=...`)
- `Config_Environment` (production vs development site URLs)

**Example Additional Compose Actions:**
```
Config_Max_Items: 500
Config_Scan_Depth: outputs('Get_Meeting_Record')?['body/crad9_level']
Config_Results_Top: 1000
```

---

## 📚 Related Documentation

- `COMPLETE_STEP_BY_STEP_FLOW_BUILD.html` - Full flow build guide (updated)
- `CONCAT_EXPRESSION_FOR_FILTER.md` - Concat expression reference (updated)
- `SHAREPOINT_FILTER_FIX.md` - Why site path prefix is required

---

**Last Updated:** 2026-02-23
**Version:** 1.0
**Changes:** Added Config_List_Title and Config_Site_Path_Prefix Compose actions
