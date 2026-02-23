# Meeting Form Customization Guide

## Overview

This guide walks you through customizing the Meeting form in Power Apps to create a comprehensive meeting management interface with tabs for Details, Agenda Items, Meeting Members, and Permission Scans.

## Prerequisites

- **Solution Imported:** `CRMPowerBISharePointIntegration_1_0_0_12_Complete.zip`
- **Flows Configured:** All connection references authorized
- **Tables Created:** Meeting, Agenda Item, Meeting Contact, Scan, Item Permission

## What's Already in the Solution

✅ **Conflict of Interest Field** - Added to Agenda Item table (`crad9_hasconflictofinterest`)
✅ **CreateMeetingSPFolder Flow** - Auto-creates meeting folders when `crad9_isuserallowedspfolder = true`
✅ **CreateAgendaItemSPFolder Flow** - Auto-creates subfolders for agenda items
✅ **ScanMeetingFolderPermissions Flow** - Scans and records SharePoint permissions

---

## Part 1: Customize the Meeting Form

### Step 1: Open the Form Editor

1. Go to **https://make.powerapps.com**
2. Select your environment: **Dev**
3. Navigate to **Solutions** > **CRM-Power BI-SharePoint Integration**
4. Find and click on **Meeting** table
5. Click on **Forms** tab
6. Click on the **Main** form (should say "Information" or "Main Form")
7. Click **Edit form** (opens in form designer)

### Step 2: Add Tabs to the Form

**Add Tab 1: Meeting Details** (rename existing tab)
1. Click on the existing tab (usually called "General")
2. In the properties panel, rename it to **"Meeting Details"**
3. Keep the existing section or add sections as needed

**Add Tab 2: Agenda Items**
1. Click **+ Component** > **1-column tab**
2. Rename tab to **"Agenda Items"**
3. Remove the default section

**Add Tab 3: Meeting Members**
1. Click **+ Component** > **1-column tab**
2. Rename tab to **"Meeting Members"**
3. Remove the default section

**Add Tab 4: Permission Scans**
1. Click **+ Component** > **1-column tab**
2. Rename tab to **"Permission Scans"**
3. Remove the default section

### Step 3: Configure Meeting Details Tab

**Add these fields to the form:**

| Field Name | Display Name | Type | Notes |
|------------|--------------|------|-------|
| `crad9_newcolumn` | Meeting Name | Text | Primary field |
| `crad9_meetingstartdate` | Meeting Start Date | DateTime | |
| `crad9_meetingenddate` | Meeting End Date | DateTime | |
| `crad9_level` | Permission Level | Integer | For permission scanning depth |
| `crad9_isuserallowedspfolder` | Create SharePoint Folder | Boolean | Triggers folder creation |
| `crad9_spfoldercreated` | SP Folder Created | Boolean | Read-only status |
| `crad9_folderurl` | Folder URL | URL | Make it a hyperlink |
| `crad9_lastscandate` | Last Scan Date | DateTime | Read-only |

**Recommended Layout:**
```
Section: Basic Information
  - Meeting Name (full width)
  - Meeting Start Date | Meeting End Date (2 columns)
  - Permission Level (1 column)

Section: SharePoint Integration
  - Create SharePoint Folder (checkbox)
  - SP Folder Created (read-only checkbox)
  - Folder URL (hyperlink - full width)
  - Last Scan Date (read-only)
```

**Add "Run Permission Scan" Button (Optional):**
1. Click **+ Component** > **Button**
2. Label: "Run Permission Scan"
3. In button properties, set Action: **Run workflow**
4. Select workflow: **ScanMeetingFolderPermissions**
5. Map input: Meeting ID → `crad9_meetingid`

### Step 4: Add Agenda Items Subgrid

1. Click on the **Agenda Items** tab
2. Click **+ Component** > **Subgrid**
3. Configure subgrid:
   - **Label:** Agenda Items
   - **Table:** Agenda Item (`crad9_agendaitem`)
   - **Default View:** Active Agenda Items
   - **Show related records:** Yes (filtered by Meeting lookup)
4. Enable **Editable Grid** (allows inline editing)
5. Add these columns to the view:
   - Sequence
   - Name
   - Description
   - Has Conflict of Interest (**NEW field!**)
   - Folder Created
   - SP Folder URL
6. Enable **Quick Create** form for easy agenda item addition

### Step 5: Add Meeting Members Subgrid

1. Click on the **Meeting Members** tab
2. Click **+ Component** > **Subgrid**
3. Configure subgrid:
   - **Label:** Meeting Members
   - **Table:** Meeting Contact (`crad9_meetingcontact`)
   - **Default View:** Active Meeting Contacts
   - **Show related records:** Yes (filtered by Meeting lookup)
4. Enable **Editable Grid**
5. Add these columns to the view:
   - Contact (lookup)
   - Role (Organizer/Attendee/Optional)
   - RSVP Status (Pending/Accepted/Declined/Tentative)
   - SP Access Granted
6. Enable **Quick Create** form for easy member addition

### Step 6: Add Permission Scans Subgrid

1. Click on the **Permission Scans** tab
2. Click **+ Component** > **Subgrid**
3. Configure subgrid:
   - **Label:** Permission Scan History
   - **Table:** Scan (`crad9_scan`)
   - **Default View:** Scans for this Meeting
   - **Show related records:** Yes (filtered by Meeting lookup)
4. Make this **Read-Only** (not editable)
5. Add these columns to the view:
   - Name (e.g., "Scan - Meeting Name - Timestamp")
   - Status (In Progress/Completed/Failed)
   - Scan Start Time
   - Items Scanned
   - Broken Permissions Found
   - Total Permissions Recorded
6. Add **nested subgrid** for detailed permissions:
   - When user clicks a scan, show related `crad9_itempermission` records
   - Columns: Item Name, Item Type, Principal Name, Principal Type, Permission Level

### Step 7: Configure Business Rules (Optional but Recommended)

**Business Rule 1: Validate Meeting Dates**
1. In form designer, click **Business Rules** (top menu)
2. Create new rule: "Validate Meeting Dates"
3. Condition: `Meeting End Date` < `Meeting Start Date`
4. Action: Show error message "End date must be after start date"

**Business Rule 2: Auto-Check Folder Creation for New Meetings**
1. Create new rule: "Default Folder Creation"
2. Condition: Record is new (`crad9_meetingid` is empty)
3. Action: Set `crad9_isuserallowedspfolder` = Yes

**Business Rule 3: Make Folder URL Clickable**
1. Create new rule: "Enable Folder Link"
2. Condition: `crad9_folderurl` is not empty
3. Action: Set field as hyperlink

### Step 8: Save and Publish

1. Click **Save** (top right)
2. Click **Publish** (top right)
3. Test the form by creating a new meeting record

---

## Part 2: Create Model-Driven App

### Step 1: Create the App

1. Go to **https://make.powerapps.com**
2. Click **Apps** > **+ New app** > **Model-driven**
3. Name: **Meeting Management**
4. Description: **Comprehensive meeting and permission management system**
5. Click **Create**

### Step 2: Add Tables to the App

Click **+ Add page** and add these tables:

| Table | Display Name | Include in Navigation |
|-------|--------------|----------------------|
| Meeting | Meetings | Yes |
| Agenda Item | Agenda Items | Yes |
| Meeting Contact | Meeting Members | No (accessed via meeting form) |
| Scan | Permission Scans | Yes |
| Item Permission | Permission Details | No (accessed via scan form) |
| Contact | Contacts | Yes |

### Step 3: Configure the Sitemap (Navigation)

**Meetings Area:**
- **Meetings** (main dashboard)
  - View: Active Meetings (default)
  - View: My Meetings
  - View: Upcoming Meetings (sort by start date)
- **Agenda Items**
  - View: All Agenda Items
  - View: Items with Conflicts (filter: `crad9_hasconflictofinterest = Yes`)

**Permissions Area:**
- **Permission Scans**
  - View: Recent Scans (last 30 days)
  - View: Failed Scans (for troubleshooting)
- **Permission Details**
  - View: All Permissions
  - View: Unique Permissions Only

**Administration Area:**
- **Contacts**
  - View: All Contacts
  - View: Meeting Organizers

### Step 4: Create Dashboards

**Dashboard 1: Meeting Overview**
1. Click **+ Add page** > **Dashboard**
2. Name: **Meeting Overview**
3. Add charts:
   - **Meetings This Month** (count by week)
   - **Meetings by Status** (pie chart if you add a status field)
   - **Recent Permission Scans** (list of last 5 scans)
   - **Agenda Items with Conflicts** (count of COI items)

**Dashboard 2: Permission Compliance**
1. Create new dashboard: **Permission Compliance**
2. Add charts:
   - **Permission Scans by Status** (In Progress/Completed/Failed)
   - **Items with Unique Permissions** (trend over time)
   - **Top 10 Folders by Permission Count**

### Step 5: Configure App Settings

1. Click **Settings** (gear icon)
2. **Advanced settings**:
   - Enable **Editable grids** globally
   - Enable **Quick create** forms
   - Set default view for Meetings: **Upcoming Meetings**
3. **Security roles**:
   - Assign appropriate security roles to users
   - Recommended: Basic User, System Administrator

### Step 6: Save and Publish

1. Click **Save**
2. Click **Publish**
3. Click **Play** to test the app

---

## Part 3: Testing the Complete Solution

### Test Scenario 1: Create Meeting with Auto-Folder Creation

1. Open the **Meeting Management** app
2. Click **Meetings** > **+ New**
3. Fill in:
   - Meeting Name: "Board Meeting Q1-2026"
   - Start Date: Tomorrow at 10:00 AM
   - End Date: Tomorrow at 11:30 AM
   - Permission Level: 2
   - **Create SharePoint Folder:** ✅ Yes
4. Click **Save**
5. **Expected Result:**
   - Within 1-2 minutes, `SP Folder Created` changes to ✅ Yes
   - `Folder URL` populates with SharePoint link
   - Clicking the URL opens the SharePoint folder

### Test Scenario 2: Add Agenda Items with COI Tracking

1. On the meeting form, go to **Agenda Items** tab
2. Click **+ New Agenda Item** (quick create)
3. Fill in:
   - Name: "Budget Review & Approval"
   - Sequence: 1
   - Description: "FY2026 budget approval"
   - **Has Conflict of Interest:** ✅ Yes (if applicable)
4. Click **Save**
5. **Expected Result:**
   - Agenda item appears in subgrid
   - Within 1-2 minutes, `Folder Created` = ✅ Yes
   - Subfolder created under meeting folder in SharePoint

### Test Scenario 3: Add Meeting Members

1. Go to **Meeting Members** tab
2. Click **+ New Meeting Contact**
3. Fill in:
   - Contact: Select a contact (or create new)
   - Role: Organizer
   - RSVP Status: Accepted
4. Click **Save**
5. Repeat for attendees
6. **Expected Result:**
   - All members visible in subgrid
   - Can edit roles/RSVP inline

### Test Scenario 4: Run Permission Scan

1. Go to **Meeting Details** tab
2. Click **"Run Permission Scan"** button (if added)
   - OR manually trigger the flow:
     - Go to Power Automate
     - Find **ScanMeetingFolderPermissions**
     - Click **Run** > Enter Meeting ID
3. **Expected Result:**
   - New scan record appears in **Permission Scans** tab
   - Status: In Progress → Completed
   - Shows count of items scanned and permissions found
4. Click on the scan record to see detailed permissions

---

## Part 4: Advanced Customizations (Optional)

### Add Calculated Fields

**1. Meeting Duration (calculated field)**
- Field: `crad9_meetingduration`
- Type: Whole Number
- Calculation: `DIFFINMINUTES(crad9_meetingstartdate, crad9_meetingenddate)`
- Display on form

**2. Has Conflicts Indicator (calculated/rollup)**
- Field: `crad9_hasagendaconflicts`
- Type: Boolean
- Rollup: Count of related `crad9_agendaitem` where `crad9_hasconflictofinterest = Yes`
- If count > 0, set to Yes

### Add Form Scripts (JavaScript)

**1. Auto-open SharePoint Folder**
```javascript
// On form load, add click handler to folder URL
function onFormLoad(executionContext) {
    var formContext = executionContext.getFormContext();
    var folderUrl = formContext.getAttribute("crad9_folderurl").getValue();

    if (folderUrl) {
        // Add button to open folder in new tab
        // (Implementation depends on your requirements)
    }
}
```

**2. Validate Permission Level**
```javascript
// Ensure permission level is between 1 and 10
function validatePermissionLevel(executionContext) {
    var formContext = executionContext.getFormContext();
    var level = formContext.getAttribute("crad9_level").getValue();

    if (level < 1 || level > 10) {
        formContext.getControl("crad9_level").setNotification(
            "Permission level must be between 1 and 10",
            "LEVEL_VALIDATION"
        );
    } else {
        formContext.getControl("crad9_level").clearNotification("LEVEL_VALIDATION");
    }
}
```

### Create Custom Views

**View: Meetings Needing Permission Scan**
- Filter: `Last Scan Date` is older than 7 days OR `Last Scan Date` is null
- Sort: Meeting Start Date (descending)
- Purpose: Identify meetings that haven't been scanned recently

**View: Agenda Items with Pending COI Review**
- Filter: `Has Conflict of Interest` = Yes
- Sort: Meeting (ascending), Sequence (ascending)
- Purpose: Compliance review workflow

---

## Part 5: Security and Permissions

### Security Roles

**Create custom security roles:**

**1. Meeting Organizer Role**
- Can create/edit/delete own meetings
- Can add/remove members from own meetings
- Can trigger permission scans
- **Cannot** access other users' meetings

**2. Meeting Viewer Role**
- Can view all meetings (read-only)
- Can view permission scan results
- **Cannot** create or edit meetings

**3. Compliance Officer Role**
- Can view all meetings and scans
- Can run permission scans on any meeting
- Can export permission data
- Can view COI declarations

### Field-Level Security

**Protect sensitive fields:**
- `crad9_spfoldercreated` - Read-only for all users
- `crad9_folderurl` - Read-only for all users
- `crad9_lastscandate` - Read-only for all users
- Scan status/counters - Read-only for all users

---

## Part 6: Troubleshooting

### Issue 1: Folder Not Created

**Symptoms:** `SP Folder Created` remains unchecked after saving

**Diagnosis:**
1. Check if `Create SharePoint Folder` is checked
2. Verify **CreateMeetingSPFolder** flow status:
   - Go to Power Automate > My flows
   - Find CreateMeetingSPFolder
   - Check **Run history**
3. Look for errors in the flow run

**Common Causes:**
- SharePoint connection not authorized
- Meeting name contains unsupported characters (/, \, :, ?)
- Duplicate folder name already exists
- Permissions issue in SharePoint library

**Solution:**
- Authorize SharePoint connection
- Rename meeting to remove special characters
- Manually delete duplicate folder in SharePoint
- Grant flow owner contribute access to Meetings library

### Issue 2: Agenda Subfolder Not Created

**Symptoms:** `Folder Created` on agenda item remains unchecked

**Diagnosis:**
1. Check if parent meeting has `SP Folder Created` = Yes
2. Verify **CreateAgendaItemSPFolder** flow status
3. Check if agenda item name contains special characters

**Solution:**
- Ensure meeting folder exists first (trigger CreateMeetingSPFolder)
- Wait 1-2 minutes for meeting folder creation to complete
- Rename agenda item to remove special characters

### Issue 3: Permission Scan Fails

**Symptoms:** Scan status = Failed, error message in scan record

**Common Errors:**
- "Folder URL is empty" → Meeting doesn't have folder URL
- "401 Unauthorized" → SharePoint connection not authorized
- "404 Not Found" → Folder doesn't exist in SharePoint

**Solution:**
- Verify `crad9_folderurl` is populated
- Re-authorize SharePoint connection
- Manually verify folder exists in SharePoint

### Issue 4: Connection References Not Authorized

**Symptoms:** "Connector not found" when editing flows

**Solution:**
1. Go to Solutions > Connection References
2. Click each connection reference
3. Select/create connection from dropdown
4. Save

---

## Summary Checklist

Before going live, ensure:

- [ ] All tables created and verified (Meeting, Agenda Item, Meeting Contact, Scan, Item Permission)
- [ ] COI field added to Agenda Item table
- [ ] Meeting form customized with 4 tabs
- [ ] Subgrids added for Agenda Items, Members, and Scans
- [ ] All flows imported and connections authorized:
  - [ ] CreateMeetingSPFolder
  - [ ] CreateAgendaItemSPFolder
  - [ ] ScanMeetingFolderPermissions
- [ ] Model-driven app created with proper navigation
- [ ] Security roles configured and assigned
- [ ] Test meeting created successfully
- [ ] Folder auto-creation tested and working
- [ ] Agenda items created with COI tracking
- [ ] Permission scan tested and results visible

---

## Support and Resources

**Power Apps Documentation:**
- Form Customization: https://docs.microsoft.com/powerapps/maker/model-driven-apps/create-edit-forms
- Business Rules: https://docs.microsoft.com/powerapps/maker/model-driven-apps/create-business-rules
- Model-Driven Apps: https://docs.microsoft.com/powerapps/maker/model-driven-apps/model-driven-app-overview

**Power Automate Documentation:**
- Cloud Flows: https://docs.microsoft.com/power-automate/flow-types
- Dataverse Triggers: https://docs.microsoft.com/power-automate/dataverse/overview

**Troubleshooting:**
- Check flow run history in Power Automate
- Review Dataverse logs for errors
- Test SharePoint connections manually

---

**Last Updated:** 2026-02-22
**Version:** 1.0
**Solution Version:** 1.0.0.12
