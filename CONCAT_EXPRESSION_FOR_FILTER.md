# Concat Expression for SharePoint Filter

## 🎯 Purpose
Build the complete server-relative path for the SharePoint filter by combining the site path with the folder path.

## ⭐ UPDATED (2026-02-23): Configuration Variables

This document has been updated to use **Compose actions for configuration values** instead of hardcoded values.

**New Compose Actions Required:**
- **Action 7a:** `Config_List_Title` - Value: `Meetings`
- **Action 7b:** `Config_Site_Path_Prefix` - Value: `/sites/Permission-Scanner-Test`

See `FLOW_CONFIGURATION_VARIABLES_UPDATE.md` for complete setup instructions.

## 📝 Expression for Action 12 Uri Field

Instead of typing the full Uri as plain text, you can build it dynamically using concat().

### **Option 1: Concat for the Entire Uri (Recommended) - UPDATED**

**⭐ NEW VERSION (uses Config variables):**

**Use this in the Uri field with Expression tab:**

```
concat('_api/web/lists/GetByTitle(''',outputs('Config_List_Title'),''')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''',outputs('Config_Site_Path_Prefix'),'/',outputs('Set_Folder_Path'),''')&$top=500')
```

**Explanation:**
- Single quotes inside concat need to be doubled when wrapping static text: `''Meetings''`
- Now uses `outputs('Config_List_Title')` instead of hardcoded `'Meetings'`
- Now uses `outputs('Config_Site_Path_Prefix')` instead of hardcoded `'/sites/Permission-Scanner-Test'`
- Results in: `_api/web/lists/GetByTitle('Meetings')/items?...&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]')&$top=500`

---

**OLD VERSION (hardcoded values - not recommended):**

```
concat('_api/web/lists/GetByTitle(''Meetings'')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''/sites/Permission-Scanner-Test/',outputs('Set_Folder_Path'),''')&$top=500')
```

### **Option 2: Just the Filter Part (If you want to be more explicit)**

If you only want to concat the filter value:

**Step 1:** Add a new Compose action after `Set_Folder_Path`
- **Name**: `Build_Full_Path`
- **Expression**:
```
concat('/sites/Permission-Scanner-Test/',outputs('Set_Folder_Path'))
```

**Step 2:** Then in Action 12 Uri field, type directly:
```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'@{outputs('Build_Full_Path')}')&$top=500
```

### **Option 3: Simplest - Direct Entry (What I Recommend) - UPDATED**

**⭐ NEW VERSION (uses Config variables):**

**Just type this directly in the Uri field (NO Expression tab needed):**

```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'@{outputs('Config_Site_Path_Prefix')}/@{outputs('Set_Folder_Path')}')&$top=500
```

Power Automate will automatically parse the `@{...}` as dynamic content.

**What Changed:**
- `'Meetings'` → `'@{outputs('Config_List_Title')}'`
- `'/sites/Permission-Scanner-Test/` → `'@{outputs('Config_Site_Path_Prefix')}/`

---

**OLD VERSION (hardcoded values - not recommended):**

```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/@{outputs('Set_Folder_Path')}')&$top=500
```

## 🔧 Step-by-Step: Using Concat (Option 1) - UPDATED

**⭐ PREREQUISITE:** First create Actions 7a and 7b:
- **Action 7a:** `Config_List_Title` (value: `Meetings`)
- **Action 7b:** `Config_Site_Path_Prefix` (value: `/sites/Permission-Scanner-Test`)

See `FLOW_CONFIGURATION_VARIABLES_UPDATE.md` for detailed setup.

---

**Then update Action 12:**

1. **Go to Action 12**: Send_HTTP_to_SharePoint
2. **Click in the Uri field**
3. **Click "Expression" tab** at the bottom
4. **Copy and paste this entire expression** (NEW VERSION):

```
concat('_api/web/lists/GetByTitle(''',outputs('Config_List_Title'),''')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''',outputs('Config_Site_Path_Prefix'),'/',outputs('Set_Folder_Path'),''')&$top=500')
```

5. **Click OK**
6. **Save the flow**

---

**OLD VERSION (hardcoded - not recommended):**

```
concat('_api/web/lists/GetByTitle(''Meetings'')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''/sites/Permission-Scanner-Test/',outputs('Set_Folder_Path'),''')&$top=500')
```

## 📊 What Each Option Produces

All three options produce the same final result:

**When `Set_Folder_Path` = `Meetings/Budget Meeting- [Urgent]`**

Final Uri:
```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]')&$top=500
```

## ⚠️ Important Notes

### **Escaping Single Quotes in Concat**

In Power Automate expressions, single quotes inside a string must be doubled:

- ❌ Wrong: `concat('GetByTitle('Meetings')')`
- ✅ Correct: `concat('GetByTitle(''Meetings'')')`

### **Why Option 3 is Easiest**

Power Automate's Uri field automatically recognizes `@{...}` syntax when you type it directly, so you don't need concat() at all. This is the **recommended approach** because:

1. ✅ Easier to read
2. ✅ Less escaping needed
3. ✅ Easier to debug
4. ✅ Same result

## 🧪 Test Expression

To test if your expression is correct, add a Compose action after Action 12:

**Name**: Debug_Uri
**Expression**:
```
concat('_api/web/lists/GetByTitle(''Meetings'')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''/sites/Permission-Scanner-Test/',outputs('Set_Folder_Path'),''')&$top=500')
```

Run the flow and check the output - it should show the complete Uri with the folder path filled in.

## 📝 Summary - UPDATED

**Best approach**: Use Option 3 (direct entry with `@{...}` syntax)

**If you must use concat**: Use Option 1 expression (NEW VERSION with Config variables)

**⭐ NEW Full concat expression (recommended):**
```
concat('_api/web/lists/GetByTitle(''',outputs('Config_List_Title'),''')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''',outputs('Config_Site_Path_Prefix'),'/',outputs('Set_Folder_Path'),''')&$top=500')
```

**OLD Full concat expression (hardcoded - not recommended):**
```
concat('_api/web/lists/GetByTitle(''Meetings'')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,''/sites/Permission-Scanner-Test/',outputs('Set_Folder_Path'),''')&$top=500')
```

---

## 🔗 Related Documentation

- `FLOW_CONFIGURATION_VARIABLES_UPDATE.md` - Setup guide for Config Compose actions
- `COMPLETE_STEP_BY_STEP_FLOW_BUILD.html` - Full flow build instructions (updated)
- `SHAREPOINT_FILTER_FIX.md` - Why site path prefix is required
