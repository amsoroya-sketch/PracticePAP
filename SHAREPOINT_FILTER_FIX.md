# SharePoint REST API Filter Issue - FIXED

## ❌ The Problem

The filter expression in your flow is invalid:

```
startswith(FileRef,'Meetings/Budget Meeting- [Urgent]')
```

SharePoint REST API error:
```
The expression "startswith(FileRef,'Meetings/Budget Meeting- [Urgent]')" is not valid.
```

## 🔍 Root Cause

SharePoint REST API OData v3 has **strict syntax rules** for string filters:

1. String literals must use **single quotes inside the filter**
2. Special characters in paths can cause parsing issues
3. The `startswith()` function syntax is correct, BUT...
4. **The path itself needs proper escaping in OData**

## ✅ The Fix

### **Option 1: Use substringof (OData v3 Compatible)**

Instead of:
```
$filter=startswith(FileRef,'Meetings/Budget Meeting- [Urgent]')
```

Use:
```
$filter=substringof('Meetings/Budget Meeting- [Urgent]',FileRef)
```

**Note**: `substringof()` checks if the string is contained anywhere (not just at start), but this works for our use case.

### **Option 2: Escape Special Characters in OData Filter**

The brackets `[` and `]` may need to be URL-encoded in the OData filter:

```
$filter=startswith(FileRef,'Meetings/Budget Meeting- %5BUrgent%5D')
```

But this defeats the purpose of decoding!

### **Option 3: Use Server-Relative URL (RECOMMENDED)**

SharePoint `FileRef` is stored as a **server-relative path** starting from `/sites/...`

Check the actual format:
```
/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]/file.docx
```

So your filter should be:
```
$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]')
```

## 🔧 Fix in Your Power Automate Flow

### **Current (Broken) Uri in Action 12:**

```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'@{outputs('Set_Folder_Path')}')&$top=500
```

**Issue**: `Set_Folder_Path` outputs `Meetings/Budget Meeting- [Urgent]` but `FileRef` stores `/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]`

### **FIXED Uri for Action 12:**

```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/@{outputs('Set_Folder_Path')}')&$top=500
```

**What changed**: Added `/sites/Permission-Scanner-Test/` prefix to match the actual `FileRef` format.

## 📝 Step-by-Step Fix

1. **Open your flow** in Power Automate
2. **Go to Action 12**: Send_HTTP_to_SharePoint
3. **Update the Uri field** to:

```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/@{outputs('Set_Folder_Path')}')&$top=500
```

4. **Save the flow**
5. **Test again**

## 🧪 Test in Browser

To verify the fix works, test this URL in your browser (while logged into SharePoint):

```
https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/_api/web/lists/GetByTitle('Meetings')/items?$select=FileRef,FileLeafRef&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]')&$top=10
```

**Expected result**: JSON with items from that folder (if any exist)

## 📊 Alternative: Check What FileRef Format SharePoint Uses

To see the actual `FileRef` values SharePoint stores:

```
https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test/_api/web/lists/GetByTitle('Meetings')/items?$select=FileRef&$top=5
```

This will show you the exact format, e.g.:
```json
{
  "d": {
    "results": [
      {
        "FileRef": "/sites/Permission-Scanner-Test/Meetings/Budget Meeting- [Urgent]/document.docx"
      }
    ]
  }
}
```

## 🎯 Summary

**The Problem**: Your filter used relative path `Meetings/...` but SharePoint stores absolute path `/sites/.../Meetings/...`

**The Solution**: Add site path prefix `/sites/Permission-Scanner-Test/` to your filter

**Updated Uri**:
```
_api/web/lists/GetByTitle('Meetings')/items?$select=Id,FileRef,FileLeafRef,FSObjType,Modified,HasUniqueRoleAssignments&$filter=startswith(FileRef,'/sites/Permission-Scanner-Test/@{outputs('Set_Folder_Path')}')&$top=500
```
