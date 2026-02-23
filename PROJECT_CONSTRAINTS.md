# Power Platform Project Constraints & Best Practices
## Version: 1.0.0 | Last Updated: 2026-02-23

## 🎯 Project Context
This project focuses on Power Platform solutions integrating Power Automate, SharePoint, Dataverse, and Model-Driven/Canvas Apps with emphasis on permission management and meeting workflows.

---

## 🔒 Security & Authentication (CRITICAL)

### 1. Connection Management
**ALWAYS**:
- Use OAuth 2.0 connections for SharePoint and Dataverse
- Store credentials in Azure Key Vault or Power Platform environment variables
- Use managed identities for automated flows
- Validate connection references before flow deployment

**NEVER**:
- Hardcode credentials in flows, scripts, or configuration files
- Share connection strings in documentation
- Use personal accounts for production flows
- Skip connection verification steps

**Example (Correct Pattern)**:
```json
{
  "connectionReferences": {
    "shared_sharepointonline": {
      "runtimeSource": "embedded",
      "connection": {
        "connectionReferenceLogicalName": "crad9_sharepoint_connection"
      }
    }
  }
}
```

### 2. Data Protection
- All PHI/PII data must use field-level encryption
- Enable SharePoint Information Rights Management (IRM)
- Implement row-level security in Dataverse
- Audit all data access operations

---

## 📊 Dataverse Schema Standards

### 1. Naming Conventions
**Tables (Entities)**:
- Pattern: `<publisher_prefix>_<tablename>`
- Example: `crad9_meeting`, `crad9_agendaitem`
- Never use spaces or special characters

**Columns (Fields)**:
- Pattern: `<publisher_prefix>_<columnname>`
- Example: `crad9_meetingtitle`, `crad9_folderurl`
- Use camelCase after prefix
- Date fields: suffix with `_date` (e.g., `crad9_meetingdate`)
- Lookup fields: suffix with `_id` (e.g., `crad9_meetingid`)

**Relationships**:
- One-to-Many: `1:N <ParentTable>_<ChildTable>`
- Many-to-One: `N:1 <ChildTable>_<ParentTable>`
- Example: `1:N crad9_meeting_agendaitem`

### 2. Field Types & Constraints
```python
# Correct field definitions (Python SDK)
{
    "LogicalName": "crad9_folderurl",
    "SchemaName": "crad9_FolderURL",
    "DisplayName": {"@odata.type": "Microsoft.Dynamics.CRM.Label", "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": "Folder URL", "LanguageCode": 1033}]},
    "AttributeType": "String",
    "AttributeTypeName": {"Value": "StringType"},
    "MaxLength": 500,
    "Format": "Url"
}
```

**Common Field Formats**:
- URLs: `MaxLength: 500`, `Format: "Url"`
- Emails: `MaxLength: 100`, `Format: "Email"`
- Dates: Use `DateTimeType` with `DateTimeBehavior: "UserLocal"`
- Currency: Use `MoneyType` with precision 2

### 3. Solution Packaging
- Publisher prefix: `crad9` (customize per organization)
- Version format: `Major.Minor.Build.Revision` (e.g., `1.0.0.12`)
- Always include dependencies in `solution.xml`
- Export as **managed** solutions for production

---

## 🔄 Power Automate Flow Standards

### 1. Flow Naming & Organization
**Naming Pattern**: `<Category>-<Action>-<Description>`
- Example: `Meeting-Create-SharePointFolders`
- Example: `PermissionScanner-Scan-LibraryPermissions`

**Categories**:
- `Meeting`: Meeting lifecycle flows
- `PermissionScanner`: Permission analysis flows
- `Notification`: Alert and email flows
- `Scheduled`: Time-based triggers

### 2. Variable Initialization (CRITICAL)
**ALWAYS initialize configuration variables at the start of flows**:

```json
{
  "varSharePointSiteURL": {
    "type": "String",
    "value": "@parameters('SharePointSiteURL')"
  },
  "varMeetingsLibraryName": {
    "type": "String",
    "value": "Meetings"
  },
  "varAgendaItemsTable": {
    "type": "String",
    "value": "crad9_agendaitems"
  }
}
```

**Variable Naming**:
- Prefix with `var` for flow variables
- Prefix with `param` for parameters
- Use camelCase: `varFolderName`, `paramMeetingID`

### 3. Error Handling Pattern
**Every action must have Configure Run After settings**:

```json
{
  "runAfter": {
    "PreviousAction": ["Succeeded"]
  },
  "type": "Compose",
  "inputs": {
    "ErrorMessage": "@{body('PreviousAction')?['error']?['message']}"
  }
}
```

**Scope-Based Error Handling**:
- Wrap related actions in `Scope` containers
- Add parallel `Scope-ErrorHandler` with `runAfter: ["Failed", "TimedOut"]`
- Log errors to Dataverse table `crad9_errorlog`

### 4. SharePoint Operations
**Get Items Filter Queries**:
```odata
# Correct: Use single quotes for string literals
FolderURL eq 'https://site.sharepoint.com/folder'

# Correct: Encode special characters
FolderURL eq '@{encodeUriComponent(variables('varFolderURL'))}'

# Incorrect: Double quotes (will fail)
FolderURL eq "https://site.sharepoint.com/folder"
```

**Pagination**:
- Always set threshold: `"top": 5000`
- Enable `"isPaged": true` for large libraries
- Use `@outputs('Get_items')?['body/value']` to access results

**Permission Operations**:
- Use `Send an HTTP request to SharePoint` action
- Endpoint: `_api/web/lists/getbytitle('Meetings')/items(@{items('Apply_to_each')?['ID']})/roleassignments`
- Method: `GET`
- Headers: `Accept: application/json;odata=verbose`

### 5. Dataverse Operations (Jan 2026 Updates)
**Create Records**:
```json
{
  "logicalName": "crad9_meeting",
  "crad9_meetingtitle": "@triggerOutputs()?['body/crad9_meetingtitle']",
  "crad9_meetingdate": "@triggerOutputs()?['body/crad9_meetingdate']",
  "_crad9_parentmeeting_value": "@triggerOutputs()?['body/_crad9_parentmeeting_value']"
}
```

**Lookup Field Pattern** (CRITICAL):
- Input: `_<fieldname>_value` (e.g., `_crad9_meetingid_value`)
- GUID format only (no curly braces in some contexts)
- Use `@outputs('Get_record')?['body/<lookupfield>']` to retrieve

**Expand Related Records**:
```
$expand=crad9_meeting_agendaitem($select=crad9_agendaitemid,crad9_title)
```

---

## 📁 SharePoint Configuration

### 1. Library Structure
**Meetings Library**:
- Default view: `AllItems.aspx`
- Folder structure: `/<Year>/<MeetingTitle>_<Date>/`
- Required columns:
  - `MeetingID` (Lookup to Dataverse)
  - `FolderURL` (Hyperlink)
  - `PermissionLevel` (Choice: Read, Contribute, Edit, Full Control)

**Document Sets** (if used):
- Content type inheritance required
- Metadata propagation enabled
- Custom welcome page template: `WelcomePage.aspx`

### 2. Permission Levels (Jan 2026 Standard)
| Level | SharePoint Role | Dataverse Equivalent |
|-------|----------------|---------------------|
| Read | Limited Access | Basic User |
| Contribute | Contribute | Basic User + Create |
| Edit | Edit | Basic User + Write |
| Full Control | Full Control | System Administrator |

**Permission Scanner Requirements**:
- Scan depth: 2 levels (library → folder → files)
- Store in `crad9_permissionscan` table
- Columns: `PrincipalName`, `RoleDefinition`, `ItemPath`, `ScanDate`

---

## 🧪 Testing & Validation Standards

### 1. Pre-Deployment Checklist
- [ ] All connections authorized and valid
- [ ] Flow checker shows 0 errors, 0 warnings
- [ ] Test with minimum 3 sample records
- [ ] Error handlers trigger correctly (simulate failures)
- [ ] Performance: <30 seconds for single-item operations
- [ ] Pagination tested with >5000 items

### 2. Python Script Standards
**Required Headers**:
```python
#!/usr/bin/env python3
"""
Script: <name>.py
Purpose: <description>
Dependencies: msal, requests, python-dotenv
Environment: Requires .env with TENANT_ID, CLIENT_ID, CLIENT_SECRET
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
```

**Error Handling**:
```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    sys.exit(1)
```

### 3. Shell Script Standards
**Bash Script Template**:
```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check dependencies
command -v pac >/dev/null 2>&1 || { log_error "PAC CLI not installed"; exit 1; }
```

---

## 🚀 Deployment Workflow

### 1. Solution Export Process
```bash
# 1. Export unmanaged solution
pac solution export --name CRMPowerBISharePointIntegration --path ./export --managed false

# 2. Unpack for version control
pac solution unpack --zipfile ./export/solution.zip --folder ./src

# 3. Create managed solution
pac solution pack --zipfile ./managed/solution.zip --folder ./src --processCanvasApps

# 4. Import to target environment
pac solution import --path ./managed/solution.zip --async --activate-plugins
```

### 2. Flow Activation Sequence
1. Import solution (flows remain off)
2. Configure connection references
3. Activate flows in dependency order:
   - Data flows first (Meeting-Create)
   - Dependent flows second (PermissionScanner)
   - Notification flows last

### 3. Version Increment Rules
- **Patch (0.0.0.X)**: Bug fixes, no schema changes
- **Minor (0.X.0.0)**: New features, backward compatible
- **Major (X.0.0.0)**: Breaking changes, schema modifications

---

## 🔍 Common Anti-Patterns to Avoid

### ❌ NEVER DO THIS:
1. **Hardcoded URLs in flows**
   ```json
   // Bad
   "siteUrl": "https://abctest179.sharepoint.com/sites/Meeting-Site"

   // Good
   "siteUrl": "@parameters('SharePointSiteURL')"
   ```

2. **Missing null checks**
   ```json
   // Bad
   "@outputs('Get_item')['FolderURL']"

   // Good
   "@{coalesce(outputs('Get_item')?['body/FolderURL'], 'https://default.url')}"
   ```

3. **Unencoded filter queries**
   ```odata
   # Bad (fails with spaces/special chars)
   Title eq '@{variables('varTitle')}'

   # Good
   Title eq '@{encodeUriComponent(variables('varTitle'))}'
   ```

4. **Ignoring pagination**
   ```json
   // Bad: Gets only first 100 items
   "Get_items": { "top": 100 }

   // Good: Handles all items
   "Get_items": { "top": 5000, "isPaged": true }
   ```

5. **Generic error messages**
   ```json
   // Bad
   "errorMessage": "An error occurred"

   // Good
   "errorMessage": "Failed to create folder: @{outputs('Create_folder')?['error']?['message']}"
   ```

---

## 📚 Required Reading Before Starting

### New Team Members:
1. Read this document entirely
2. Review existing flow: `Meeting-Create-SharePointFolders` in Workflows/
3. Study `provision_dataverse_schema.py` for schema patterns
4. Run `test_workflow_execution.py` to understand testing

### Before Creating New Flows:
1. Check existing flows for similar logic
2. Verify connection references in `solution.xml`
3. Review variable naming in `QUICK_REFERENCE_CONFIG_VARIABLES.md`
4. Validate filter query syntax in `SHAREPOINT_FILTER_FIX.md`

### Before Modifying Schema:
1. Export current solution as backup
2. Document changes in migration script
3. Test in dev environment first
4. Update `verify_schema.py` validation rules

---

## 🎯 Success Criteria

### Code Quality Gates:
- [ ] 0 errors in Flow Checker
- [ ] 0 warnings in PAC CLI validation
- [ ] 100% test pass rate (Python/Bash scripts)
- [ ] Security scan: 0 hardcoded credentials
- [ ] Performance: <30s for CRUD operations
- [ ] Documentation: Inline comments for complex logic

### Pre-Commit Validation:
```bash
# Run before committing
python3 verify_schema.py          # Validates Dataverse schema
python3 test_sharepoint_filter.py # Tests filter queries
bash -n *.sh                       # Syntax check all scripts
grep -r "password\|secret\|key" --include="*.json" . # Security scan
```

---

## 📞 Support & Resources

### Official Documentation (Jan 2026):
- Power Automate: https://learn.microsoft.com/power-automate/
- Dataverse Web API: https://learn.microsoft.com/power-apps/developer/data-platform/webapi/overview
- SharePoint REST API: https://learn.microsoft.com/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service

### Project-Specific Guides:
- `BUILD_PERMISSION_SCANNER_FLOW_GUIDE.html`: Step-by-step flow creation
- `CONNECTION_AUTHORIZATION_GUIDE.md`: Connection setup
- `IMPLEMENTATION_SUMMARY.md`: Project overview

### Troubleshooting:
- Flow failures: Check `EXPRESSION_VERIFICATION_SUMMARY.md`
- SharePoint filters: See `SHAREPOINT_FILTER_FIX.md`
- Dynamic config: Read `DYNAMIC_CONFIG_EXTRACTION.md`

---

**Last Updated**: 2026-02-23
**Maintained By**: Power Platform Team
**Version**: 1.0.0
