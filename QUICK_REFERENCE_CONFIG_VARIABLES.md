# Quick Reference: Dynamic Configuration Extraction

## ⚡ Quick Summary

**What Changed:** Added 2 new Compose actions that **dynamically extract** library name and site path from the folder URL

## 🆕 New Actions to Add

### **Action 7a: Config_List_Title (DYNAMIC)**
- **Location:** After Action 7 (Set_Folder_Path)
- **Type:** Compose
- **Expression:** `outputs('Parse_Folder_URL')[5]`
- **Purpose:** Extracts library name from URL (e.g., "Meetings", "Documents")

### **Action 7b: Config_Site_Path_Prefix (DYNAMIC)**
- **Location:** After Action 7a
- **Type:** Compose
- **Expression:** `concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])`
- **Purpose:** Builds site path from URL (e.g., "/sites/Permission-Scanner-Test")

## 🔄 Actions to Update

### **Action 12: Send_HTTP_to_SharePoint**

**NEW Uri (copy entire line):**
```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'@{outputs('Config_Site_Path_Prefix')}/@{outputs('Set_Folder_Path')}')&$top=500
```

### **Action 19: Get_Item_Permissions**

**NEW Uri (copy entire line):**
```
_api/web/lists/GetByTitle('@{outputs('Config_List_Title')}')/items(@{items('Apply_to_each_Item')?['Id']})/RoleAssignments?$expand=RoleDefinitionBindings,Member
```

## ✅ 5-Minute Update Checklist

- [ ] Add Action 7a after Set_Folder_Path (Expression: `outputs('Parse_Folder_URL')[5]`)
- [ ] Add Action 7b after Action 7a (Expression: `concat('/', outputs('Parse_Folder_URL')[3], '/', outputs('Parse_Folder_URL')[4])`)
- [ ] Update Action 12 Uri with NEW version above
- [ ] Update Action 19 Uri with NEW version above
- [ ] Save flow
- [ ] Test with a meeting that has files

## 🎯 Why This Matters

**Before:** Hardcoded values like "Meetings" and "/sites/Permission-Scanner-Test"
**After:** Values extracted dynamically from folder URL

**Benefits:**
- ✅ **Zero Configuration:** Works automatically with ANY library or site
- ✅ **Multi-Library Support:** Same flow works for "Meetings", "Documents", "Shared Documents", etc.
- ✅ **Site-Agnostic:** Automatically adapts to different SharePoint sites
- ✅ **Future-Proof:** No manual updates needed when library names or sites change

**To Deploy to Different Site:**
1. Nothing! It's automatic - just use the flow with any folder URL
2. Done!

## 📚 Full Documentation

- **Dynamic Extraction Guide:** `DYNAMIC_CONFIG_EXTRACTION.md` ⭐ **START HERE**
- **Complete Flow Build:** `COMPLETE_STEP_BY_STEP_FLOW_BUILD.html`
- **Concat Options:** `CONCAT_EXPRESSION_FOR_FILTER.md`

---
**Updated:** 2026-02-23 | **Version:** 2.0 (Dynamic Extraction)
