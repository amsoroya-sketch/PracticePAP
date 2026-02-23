# Power Automate Connection Authorization Guide

## Error Message
```
Some of the connections are not authorized yet. If you just created a workflow from a template, 
please add the authorized connections to your workflow before saving.
```

## Why This Happens
When you import a flow from a solution package, the **connection references** from the original environment don't exist in your new environment. You need to create new connections and link them to the flow.

---

## Required Connections for Your Flows

Based on your imported flows, you need these connections:

| Connection Type | Purpose | Count | Used In |
|----------------|---------|-------|---------|
| **Microsoft Dataverse** | Read/write meeting, scan, agenda item, and permission records | 1 | All flows |
| **SharePoint Online** | Create folders, read items, get permissions via REST API | 1-2 | All flows |

---

## Step-by-Step Fix

### Option 1: Quick Fix (Recommended)

1. **Open the Flow in Edit Mode**
   - Go to https://make.powerautomate.com
   - Navigate to **Solutions** → Your solution
   - Find **ScanMeetingFolderPermissions** flow
   - Click **Edit**

2. **You'll See Red Warning Icons** on actions that need connections:
   - Look for **⚠️** symbols on actions like:
     - "Get Meeting Record" (Dataverse)
     - "Send_HTTP_to_SharePoint" (SharePoint)
     - "Create Scan Record" (Dataverse)

3. **Fix Each Connection:**

   **For Dataverse Actions:**
   - Click on the action with the warning (e.g., "Get Meeting Record")
   - You'll see a dropdown that says "Add new connection" or shows existing connections
   - Click **"+ Add new connection"** if you don't have one
   - Sign in with your Microsoft 365 account
   - Click **Create**
   
   **For SharePoint Actions:**
   - Click on the action with the warning (e.g., "Send_HTTP_to_SharePoint")
   - Click **"+ Add new connection"**
   - Choose authentication method:
     - **Default**: Use your account credentials (easiest)
     - **Service Principal**: Use app registration (for production)
   - Click **Create**

4. **Apply the Same Connection to All Actions:**
   - After creating a connection, the flow will ask you to select it for each action
   - Choose the **same connection** you just created for all similar actions
   - Example: Use the same Dataverse connection for "Get Meeting Record", "Create Scan Record", "Update Scan Record", etc.

5. **Save the Flow**
   - Click **Save** in the top-right corner
   - If you still see warnings, repeat steps 3-4 for any missed actions

---

### Option 2: Create Connections First (Alternative)

1. **Go to Connections Page**
   - https://make.powerautomate.com
   - Left menu → **Data** → **Connections**

2. **Create New Dataverse Connection**
   - Click **+ New connection**
   - Search for **"Microsoft Dataverse"**
   - Click on it
   - Sign in with your account
   - Connection name will be auto-generated (e.g., "Dataverse-shared-commondataservice...")

3. **Create New SharePoint Connection**
   - Click **+ New connection**
   - Search for **"SharePoint"**
   - Click on **"SharePoint Online"**
   - Sign in with your account

4. **Now Go Back to Your Flow and Assign These Connections**
   - Edit your flow
   - For each action, select the connections you just created from the dropdown

---

## Common Issues and Solutions

### Issue 1: "You don't have permission to access this connection"

**Cause:** The connection was created by someone else or in a different environment.

**Solution:**
- Delete the old connection reference
- Create a **new connection** using your own account
- Re-assign it to the flow

### Issue 2: "Connection not found"

**Cause:** The connection reference logical name doesn't match any existing connection.

**Solution:**
- In the flow editor, click on each action
- From the dropdown, select **"Add new connection"**
- This will create a fresh connection with the correct reference

### Issue 3: SharePoint HTTP Request failing with 403 Forbidden

**Cause:** Your account doesn't have permissions on the SharePoint site.

**Solution:**
- Go to https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test
- Click **Settings** (gear icon) → **Site permissions**
- Verify you have at least **Edit** permissions
- If not, ask the site owner to add you
- After getting permissions, re-create the SharePoint connection in Power Automate

### Issue 4: Multiple SharePoint connections showing (shared_sharepointonline, shared_sharepointonline-1)

**Cause:** Some flows use multiple SharePoint connections for different sites or authentication methods.

**Solution:**
- You can use the **same SharePoint connection** for all actions
- Just select the same connection from the dropdown for all SharePoint actions
- The "runtimeSource: invoker" means it uses the current user's credentials

---

## Verification Steps

After fixing connections, verify they work:

1. **Test the Flow Manually**
   - Click **Test** in the top-right corner
   - Select **"Manually"**
   - Click **Test**
   - Provide a valid Meeting ID (GUID)
   - Click **Run flow**

2. **Check Run History**
   - After running, check if all actions succeeded (green checkmarks ✓)
   - If any action fails with "Unauthorized" or "Forbidden", that connection needs to be re-authorized

3. **Verify SharePoint Access**
   - The SharePoint connection must have access to:
     - Site: https://ABCTest179.sharepoint.com/sites/Permission-Scanner-Test
     - Library: "Meetings"
   - Test by manually opening that URL in your browser

---

## Connection Details from Your Flows

### Flow: ScanMeetingFolderPermissions

**Connection 1: Dataverse (shared_commondataserviceforapps)**
- **Used in:**
  - Get_Meeting_Record
  - Create_Scan_Record
  - Update_Scan_Complete
  - Update_Scan_Failed
  - Create_Permission_Record
- **Permissions needed:** Read/Write on:
  - crad9_meetings
  - crad9_scans
  - crad9_itempermissions

**Connection 2: SharePoint (shared_sharepointonline)**
- **Used in:**
  - Send_HTTP_to_SharePoint (fetch items)
  - Get_Item_Permissions (fetch role assignments)
- **Permissions needed:**
  - Read access to SharePoint site
  - API access (/_api/web/lists/...)
  - Full Control permissions to read RoleAssignments

---

## Quick Checklist

Before saving the flow, ensure:

- [ ] All actions have connections assigned (no ⚠️ warnings)
- [ ] Dataverse connection is authorized (can you see tables in Power Apps?)
- [ ] SharePoint connection is authorized (can you access the site in browser?)
- [ ] Your account has permissions on the SharePoint site
- [ ] Flow saves without errors
- [ ] Test run completes successfully

---

## Still Having Issues?

If you're still seeing connection errors after following these steps:

1. **Export the flow** (to save your work)
2. **Delete the flow** from the solution
3. **Re-import the solution** and follow Option 1 immediately
4. **Don't skip any warning signs** - fix each one as you see it

---

## Visual Guide: Where to Find Connection Settings

```
Power Automate Flow Editor
├─ Top Bar
│  ├─ Save (click after fixing connections)
│  └─ Test (verify connections work)
│
├─ Left Panel (Flow steps)
│  ├─ Trigger
│  └─ Actions (click each to see connection dropdown)
│     ├─ Get Meeting Record ⚠️
│     │  └─ Connection: [Select here] ← Fix this
│     ├─ Create Scan Record ⚠️
│     │  └─ Connection: [Select here] ← Fix this
│     └─ Send HTTP to SharePoint ⚠️
│        └─ Connection: [Select here] ← Fix this
│
└─ Right Panel (Action details)
   └─ Connection dropdown appears here when you click an action
```

---

**Last Updated:** 2026-02-23  
**For Solution:** CRMPowerBISharePointIntegration v1.0.0.12  
**Flows Affected:** All 5 flows in the solution
