# Dynamic Configuration Extraction from Folder URL

## 🎯 Purpose

Extract the SharePoint list title and site path prefix **dynamically** from the folder URL instead of hardcoding them.

## 📊 URL Structure Analysis

**Example Folder URL:**
```
https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]
```

**After Parse_Folder_URL (Action 5):**
```javascript
[
  0: "https:",
  1: "",
  2: "ABCTest179.sharepoint.com",
  3: "sites",
  4: "Permission-Scanner-Test",
  5: "Meetings",              ← List Title (Library Name)
  6: "Budget Meeting- [Urgent]"
]
```

**What We Need to Extract:**
- **List Title:** Index [5] = `"Meetings"`
- **Site Path Prefix:** `/sites/Permission-Scanner-Test` = `/` + [3] + `/` + [4]

---

## 🔄 Updated Actions

### **Action 7a: Config_List_Title (DYNAMIC)**

**Purpose:** Extract the SharePoint library name from the parsed URL

**Expression:**
```javascript
outputs('Parse_Folder_URL')[5]
```

**What this does:**
- Grabs the 6th element (index 5) from the parsed URL array
- This is always the library name (e.g., "Meetings", "Documents", "Shared Documents")

**Example:**
```
URL: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget Meeting
Array[5]: "Meetings"
```

---

### **Action 7b: Config_Site_Path_Prefix (DYNAMIC)**

**Purpose:** Build the site path prefix dynamically from parsed URL parts

**Expression:**
```javascript
concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])
```

**What this does:**
- Combines: `/` + "sites" + `/` + "Permission-Scanner-Test"
- Results in: `/sites/Permission-Scanner-Test`

**Example:**
```
URL: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget Meeting
Array[3]: "sites"
Array[4]: "Permission-Scanner-Test"
Result: "/sites/Permission-Scanner-Test"
```

---

## 📝 Complete Action Instructions

### **Action 7a: Config_List_Title**

1. **Add After:** Action 7 (Set_Folder_Path)
2. **Type:** Compose (Data Operations)
3. **Inputs (Expression Tab):**
   ```javascript
   outputs('Parse_Folder_URL')[5]
   ```
4. **Rename to:** `Config_List_Title`

**What You'll See:**
- When you test the flow, this will show: `Meetings` (or whatever your library name is)

---

### **Action 7b: Config_Site_Path_Prefix**

1. **Add After:** Action 7a
2. **Type:** Compose
3. **Inputs (Expression Tab):**
   ```javascript
   concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])
   ```
4. **Rename to:** `Config_Site_Path_Prefix`

**What You'll See:**
- When you test the flow, this will show: `/sites/Permission-Scanner-Test`

---

## 🔧 Updated Action 12 Uri

**No changes needed!** Still uses the same references:

```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'@{outputs('Config_Site_Path_Prefix')}/@{outputs('Set_Folder_Path')}')&$top=500
```

The difference is that now these values are **extracted dynamically** instead of hardcoded!

---

## 🔧 Updated Action 19 Uri

**No changes needed!** Still uses the same reference:

```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items(@{items('Apply_to_each_Item')?['Id']})/RoleAssignments?$expand=RoleDefinitionBindings,Member
```

---

## ✅ Benefits of Dynamic Extraction

### **Before (Static Config):**
```javascript
// Action 7a
Meetings  // Hardcoded value

// Action 7b
/sites/Permission-Scanner-Test  // Hardcoded value
```

**Problem:**
- Must manually change for different libraries or sites
- Error-prone if URL structure changes

### **After (Dynamic Extraction):**
```javascript
// Action 7a
outputs('Parse_Folder_URL')[5]  // Automatically extracts from URL

// Action 7b
concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])  // Builds from URL
```

**Benefits:**
- ✅ **Fully Dynamic:** Works with ANY library name automatically
- ✅ **Zero Configuration:** No manual updates needed
- ✅ **Multi-Library Support:** Can scan "Documents", "Meetings", "Shared Documents", etc.
- ✅ **Site-Agnostic:** Works across different SharePoint sites automatically
- ✅ **Future-Proof:** Adapts to URL changes automatically

---

## 🧪 Testing Examples

### **Test Case 1: Meetings Library**
```
Input URL: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Meetings/Budget Meeting
Config_List_Title: "Meetings"
Config_Site_Path_Prefix: "/sites/Permission-Scanner-Test"
✅ Works!
```

### **Test Case 2: Documents Library**
```
Input URL: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/Documents/HR Files
Config_List_Title: "Documents"
Config_Site_Path_Prefix: "/sites/Permission-Scanner-Test"
✅ Works automatically - no flow changes needed!
```

### **Test Case 3: Different Site**
```
Input URL: https://ABCTest179.sharepoint.com/sites/MyOtherSite/Shared Documents/Projects
Config_List_Title: "Shared Documents"
Config_Site_Path_Prefix: "/sites/MyOtherSite"
✅ Works automatically - no flow changes needed!
```

---

## 📋 URL Structure Assumptions

This approach assumes folder URLs follow this pattern:
```
https://{tenant}.sharepoint.com/sites/{site-name}/{library-name}/{folder-path}
  [0]   [1]          [2]            [3]      [4]           [5]          [6+]
```

**If your URLs have different structure:**
- Check the array index for library name (might not be [5])
- Adjust expressions accordingly

**To verify your URL structure:**
1. Add a Compose action after Parse_Folder_URL
2. Use expression: `outputs('Parse_Folder_URL')`
3. Run the flow and check the array output
4. Note which index contains the library name

---

## 🔄 Migration from Static to Dynamic

**If you already created static config actions (7a, 7b):**

1. **Update Action 7a:**
   - Change from: `Meetings` (static text)
   - Change to: `outputs('Parse_Folder_URL')[5]` (expression)

2. **Update Action 7b:**
   - Change from: `/sites/Permission-Scanner-Test` (static text)
   - Change to: `concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])` (expression)

3. **No changes needed to Actions 12 or 19!**

---

## 🚨 Important Notes

### **Index Safety**
The expressions assume the URL always has at least 6 elements. If folder URLs might be shorter:

**Safe version with null check:**
```javascript
// Action 7a - Safe
if(greaterOrEquals(length(outputs('Parse_Folder_URL')), 6), outputs('Parse_Folder_URL')[5], 'Meetings')

// Falls back to 'Meetings' if URL is too short
```

### **Special Characters**
Library names extracted from URLs are already URL-decoded by the split() function, so they'll have proper spaces and special characters (e.g., "Shared Documents" not "Shared%20Documents").

---

## 📚 Related Documentation

- `COMPLETE_STEP_BY_STEP_FLOW_BUILD.html` - Full flow guide (will be updated)
- `FLOW_CONFIGURATION_VARIABLES_UPDATE.md` - Original static approach
- `QUICK_REFERENCE_CONFIG_VARIABLES.md` - Quick reference (will be updated)

---

**Version:** 2.0 (Dynamic Extraction)
**Updated:** 2026-02-23
**Supersedes:** Static configuration approach in v1.0
