#!/usr/bin/env bash
# =============================================================================
# Dataverse Schema Provisioner - Meeting Management
# Uses Dataverse Web API directly (no XML import issues)
#
# Creates:
#   1. New columns on crad9_meeting
#   2. crad9_agendaitem table with all fields + relationship to crad9_meeting
#   3. crad9_meetingcontact table with fields + relationships to meeting + contact
#   4. Adds all new components to the CRMPowerBISharePointIntegration solution
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()   { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

ENV_FILE="/home/dev/Development/MSDev/.env"
[[ -f "$ENV_FILE" ]] || error ".env not found at $ENV_FILE"

while IFS='=' read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    key=$(echo "$key" | xargs); value=$(echo "$value" | xargs)
    export "$key=$value"
done < "$ENV_FILE"

TENANT_ID="${DATAVERSE_TENANT_ID}"
CLIENT_ID="${DATAVERSE_CLIENT_ID}"
CLIENT_SECRET="${DATAVERSE_CLIENT_SECRET}"
ORG_URL="${DATAVERSE_ENVIRONMENT_URL}"
API_URL="${ORG_URL}/api/data/v9.2"
SOLUTION_NAME="CRMPowerBISharePointIntegration"

echo ""
echo "============================================="
echo "  Dataverse Schema Provisioner"
echo "  Org: ${ORG_URL}"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
log "Getting Dataverse access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
    "https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}&scope=${ORG_URL}/.default")

TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))")
[[ -z "$TOKEN" ]] && { echo "$TOKEN_RESPONSE"; error "Failed to get token"; }
ok "Token obtained"

dv_get()  { curl -s -X GET  "$API_URL/$1" -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" -H "OData-MaxVersion: 4.0" -H "OData-Version: 4.0"; }
dv_post() { curl -s -X POST "$API_URL/$1" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Accept: application/json" -H "OData-MaxVersion: 4.0" -H "OData-Version: 4.0" -d "$2"; }
dv_put()  { curl -s -X PUT  "$API_URL/$1" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "Accept: application/json" -H "OData-MaxVersion: 4.0" -H "OData-Version: 4.0" -d "$2"; }

check_error() {
    local response="$1" label="$2"
    if echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'error' not in d else 1)" 2>/dev/null; then
        ok "$label"
    else
        local msg
        msg=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','unknown'))" 2>/dev/null)
        if echo "$msg" | grep -qi "already exists\|duplicate\|already defined"; then
            warn "$label - already exists (skipping)"
        else
            warn "$label FAILED: $msg"
            echo "  Response: $response" | head -c 300
        fi
    fi
}

# ---------------------------------------------------------------------------
# Helper: add attribute to existing entity
# ---------------------------------------------------------------------------
add_attribute() {
    local entity="$1" payload="$2" label="$3"
    local resp
    resp=$(dv_post "EntityDefinitions(LogicalName='${entity}')/Attributes" "$payload")
    check_error "$resp" "$label"
}

# ---------------------------------------------------------------------------
# STEP 1: Add new columns to crad9_meeting
# ---------------------------------------------------------------------------
echo ""
log "=== STEP 1: Extending crad9_meeting table ==="

# 1a. Level (integer)
add_attribute "crad9_meeting" '{
    "@odata.type": "Microsoft.Dynamics.CRM.IntegerAttributeMetadata",
    "SchemaName": "crad9_Level",
    "LogicalName": "crad9_level",
    "DisplayName": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Level","LanguageCode": 1033}]},
    "Description": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Hierarchy level of the meeting","LanguageCode": 1033}]},
    "RequiredLevel": {"Value": "None","CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
    "IsAuditEnabled": {"Value": true,"CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyauditsettings"},
    "MinValue": 0,
    "MaxValue": 2147483647,
    "Format": "None"
}' "crad9_level on crad9_meeting"

# 1b. Meeting Start Date (datetime)
add_attribute "crad9_meeting" '{
    "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
    "SchemaName": "crad9_MeetingStartDate",
    "LogicalName": "crad9_meetingstartdate",
    "DisplayName": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Meeting Start Date","LanguageCode": 1033}]},
    "Description": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Date and time when the meeting starts","LanguageCode": 1033}]},
    "RequiredLevel": {"Value": "None","CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
    "IsAuditEnabled": {"Value": true,"CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyauditsettings"},
    "Format": "DateAndTime",
    "DateTimeBehavior": {"Value": "UserLocal"}
}' "crad9_meetingstartdate on crad9_meeting"

# 1c. Meeting End Date (datetime)
add_attribute "crad9_meeting" '{
    "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
    "SchemaName": "crad9_MeetingEndDate",
    "LogicalName": "crad9_meetingenddate",
    "DisplayName": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Meeting End Date","LanguageCode": 1033}]},
    "Description": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Date and time when the meeting ends","LanguageCode": 1033}]},
    "RequiredLevel": {"Value": "None","CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
    "IsAuditEnabled": {"Value": true,"CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyauditsettings"},
    "Format": "DateAndTime",
    "DateTimeBehavior": {"Value": "UserLocal"}
}' "crad9_meetingenddate on crad9_meeting"

# 1d. Is User Allowed SP Folder (boolean)
add_attribute "crad9_meeting" '{
    "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
    "SchemaName": "crad9_IsUserAllowedSPFolder",
    "LogicalName": "crad9_isuserallowedspfolder",
    "DisplayName": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Is User Allowed SharePoint Folder","LanguageCode": 1033}]},
    "Description": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Indicates whether the user is allowed to access the SharePoint folder","LanguageCode": 1033}]},
    "RequiredLevel": {"Value": "None","CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
    "IsAuditEnabled": {"Value": true,"CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyauditsettings"},
    "DefaultValue": false,
    "OptionSet": {
        "TrueOption": {"Value": 1,"Label": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Yes","LanguageCode":1033}]}},
        "FalseOption": {"Value": 0,"Label": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"No","LanguageCode":1033}]}}
    }
}' "crad9_isuserallowedspfolder on crad9_meeting"

# 1e. SP Folder Created (boolean)
add_attribute "crad9_meeting" '{
    "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
    "SchemaName": "crad9_SPFolderCreated",
    "LogicalName": "crad9_spfoldercreated",
    "DisplayName": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "SP Folder Created","LanguageCode": 1033}]},
    "Description": {"@odata.type": "Microsoft.Dynamics.CRM.Label","LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel","Label": "Indicates whether the SharePoint folder has been provisioned","LanguageCode": 1033}]},
    "RequiredLevel": {"Value": "None","CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
    "IsAuditEnabled": {"Value": true,"CanBeChanged": true,"ManagedPropertyLogicalName": "canmodifyauditsettings"},
    "DefaultValue": false,
    "OptionSet": {
        "TrueOption": {"Value": 1,"Label": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Yes","LanguageCode":1033}]}},
        "FalseOption": {"Value": 0,"Label": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"No","LanguageCode":1033}]}}
    }
}' "crad9_spfoldercreated on crad9_meeting"

# ---------------------------------------------------------------------------
# STEP 2: Create crad9_agendaitem table
# ---------------------------------------------------------------------------
echo ""
log "=== STEP 2: Creating crad9_agendaitem table ==="

AGENDA_RESP=$(dv_post "EntityDefinitions" '{
    "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
    "SchemaName": "crad9_AgendaItem",
    "LogicalName": "crad9_agendaitem",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Agenda Item","LanguageCode":1033}]},
    "DisplayCollectionName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Agenda Items","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Agenda items for a meeting, each mapped to a SharePoint folder","LanguageCode":1033}]},
    "OwnershipType": "UserOwned",
    "IsActivity": false,
    "HasActivities": false,
    "HasNotes": false,
    "PrimaryNameAttribute": "crad9_name",
    "Attributes": [
        {
            "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
            "SchemaName": "crad9_name",
            "LogicalName": "crad9_name",
            "IsPrimaryName": true,
            "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Agenda Item Name","LanguageCode":1033}]},
            "RequiredLevel": {"Value":"ApplicationRequired","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
            "MaxLength": 200,
            "Format": "Text"
        }
    ]
}')
check_error "$AGENDA_RESP" "crad9_agendaitem table creation"

# Wait for entity to be available
sleep 5

log "Adding columns to crad9_agendaitem..."

# Sequence
add_attribute "crad9_agendaitem" '{
    "@odata.type": "Microsoft.Dynamics.CRM.IntegerAttributeMetadata",
    "SchemaName": "crad9_Sequence",
    "LogicalName": "crad9_sequence",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Order / Sequence","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Display order of the agenda item within the meeting","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "MinValue": 0, "MaxValue": 2147483647, "Format": "None"
}' "crad9_sequence on crad9_agendaitem"

# Description (memo)
add_attribute "crad9_agendaitem" '{
    "@odata.type": "Microsoft.Dynamics.CRM.MemoAttributeMetadata",
    "SchemaName": "crad9_Description",
    "LogicalName": "crad9_description",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Description","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Detailed description of the agenda item","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "MaxLength": 4000, "Format": "Text"
}' "crad9_description on crad9_agendaitem"

# SP Folder Path
add_attribute "crad9_agendaitem" '{
    "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
    "SchemaName": "crad9_SPFolderPath",
    "LogicalName": "crad9_spfolderpath",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"SharePoint Folder Path","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Relative path of the SharePoint folder for this agenda item","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "MaxLength": 500, "Format": "Text"
}' "crad9_spfolderpath on crad9_agendaitem"

# SP Folder URL
add_attribute "crad9_agendaitem" '{
    "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
    "SchemaName": "crad9_SPFolderURL",
    "LogicalName": "crad9_spfolderurl",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"SharePoint Folder URL","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Direct URL to the SharePoint folder for this agenda item","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "MaxLength": 500, "Format": "Url"
}' "crad9_spfolderurl on crad9_agendaitem"

# Folder Created (boolean)
add_attribute "crad9_agendaitem" '{
    "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
    "SchemaName": "crad9_FolderCreated",
    "LogicalName": "crad9_foldercreated",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Folder Created","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Indicates whether the SharePoint folder has been auto-created","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "DefaultValue": false,
    "OptionSet": {
        "TrueOption": {"Value":1,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Yes","LanguageCode":1033}]}},
        "FalseOption": {"Value":0,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"No","LanguageCode":1033}]}}
    }
}' "crad9_foldercreated on crad9_agendaitem"

log "Creating Meeting → AgendaItem relationship..."
REL_RESP=$(dv_post "RelationshipDefinitions" '{
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_meeting_crad9_agendaitem",
    "ReferencedEntity": "crad9_meeting",
    "ReferencingEntity": "crad9_agendaitem",
    "ReferencedAttribute": "crad9_meetingid",
    "ReferencingAttribute": "crad9_meeting",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Meeting",
        "LogicalName": "crad9_meeting",
        "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Meeting","LanguageCode":1033}]},
        "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Parent meeting this agenda item belongs to","LanguageCode":1033}]},
        "RequiredLevel": {"Value":"ApplicationRequired","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"}
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade",
        "Delete": "RemoveLink",
        "Merge": "NoCascade",
        "Reparent": "NoCascade",
        "Share": "NoCascade",
        "Unshare": "NoCascade"
    }
}')
check_error "$REL_RESP" "crad9_meeting -> crad9_agendaitem relationship"

# ---------------------------------------------------------------------------
# STEP 3: Create crad9_meetingcontact table
# ---------------------------------------------------------------------------
echo ""
log "=== STEP 3: Creating crad9_meetingcontact table ==="

MC_RESP=$(dv_post "EntityDefinitions" '{
    "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
    "SchemaName": "crad9_MeetingContact",
    "LogicalName": "crad9_meetingcontact",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Meeting Contact","LanguageCode":1033}]},
    "DisplayCollectionName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Meeting Contacts","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Junction table linking contacts to meetings with attendance details","LanguageCode":1033}]},
    "OwnershipType": "UserOwned",
    "IsActivity": false,
    "HasActivities": false,
    "HasNotes": false,
    "PrimaryNameAttribute": "crad9_name",
    "Attributes": [
        {
            "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
            "SchemaName": "crad9_name",
            "LogicalName": "crad9_name",
            "IsPrimaryName": true,
            "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Name","LanguageCode":1033}]},
            "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
            "MaxLength": 200,
            "Format": "Text"
        }
    ]
}')
check_error "$MC_RESP" "crad9_meetingcontact table creation"

sleep 5

log "Adding columns to crad9_meetingcontact..."

# Role (picklist)
add_attribute "crad9_meetingcontact" '{
    "@odata.type": "Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
    "SchemaName": "crad9_Role",
    "LogicalName": "crad9_role",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Role","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Role of this contact in the meeting","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "OptionSet": {
        "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
        "IsGlobal": false,
        "OptionSetType": "Picklist",
        "Options": [
            {"Value":117160000,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Organizer","LanguageCode":1033}]}},
            {"Value":117160001,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Attendee","LanguageCode":1033}]}},
            {"Value":117160002,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Optional","LanguageCode":1033}]}}
        ]
    }
}' "crad9_role on crad9_meetingcontact"

# RSVP Status (picklist)
add_attribute "crad9_meetingcontact" '{
    "@odata.type": "Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
    "SchemaName": "crad9_RSVPStatus",
    "LogicalName": "crad9_rsvpstatus",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"RSVP Status","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Attendance confirmation status for this contact","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "OptionSet": {
        "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
        "IsGlobal": false,
        "OptionSetType": "Picklist",
        "Options": [
            {"Value":117160000,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Pending","LanguageCode":1033}]}},
            {"Value":117160001,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Accepted","LanguageCode":1033}]}},
            {"Value":117160002,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Declined","LanguageCode":1033}]}},
            {"Value":117160003,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Tentative","LanguageCode":1033}]}}
        ]
    }
}' "crad9_rsvpstatus on crad9_meetingcontact"

# SP Access Granted (boolean)
add_attribute "crad9_meetingcontact" '{
    "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
    "SchemaName": "crad9_SPAccessGranted",
    "LogicalName": "crad9_spaccessgranted",
    "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"SP Access Granted","LanguageCode":1033}]},
    "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Indicates whether this contact has been granted SharePoint folder access","LanguageCode":1033}]},
    "RequiredLevel": {"Value":"None","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"},
    "DefaultValue": false,
    "OptionSet": {
        "TrueOption": {"Value":1,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Yes","LanguageCode":1033}]}},
        "FalseOption": {"Value":0,"Label":{"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"No","LanguageCode":1033}]}}
    }
}' "crad9_spaccessgranted on crad9_meetingcontact"

log "Creating Meeting → MeetingContact relationship..."
REL_MC_MTG=$(dv_post "RelationshipDefinitions" '{
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_meeting_crad9_meetingcontact",
    "ReferencedEntity": "crad9_meeting",
    "ReferencingEntity": "crad9_meetingcontact",
    "ReferencedAttribute": "crad9_meetingid",
    "ReferencingAttribute": "crad9_meeting",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Meeting",
        "LogicalName": "crad9_meeting",
        "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Meeting","LanguageCode":1033}]},
        "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Meeting this contact is linked to","LanguageCode":1033}]},
        "RequiredLevel": {"Value":"ApplicationRequired","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"}
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade", "Delete": "RemoveLink", "Merge": "NoCascade",
        "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"
    }
}')
check_error "$REL_MC_MTG" "crad9_meeting -> crad9_meetingcontact relationship"

log "Creating Contact → MeetingContact relationship..."
REL_MC_CON=$(dv_post "RelationshipDefinitions" '{
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "contact_crad9_meetingcontact",
    "ReferencedEntity": "contact",
    "ReferencingEntity": "crad9_meetingcontact",
    "ReferencedAttribute": "contactid",
    "ReferencingAttribute": "crad9_contact",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Contact",
        "LogicalName": "crad9_contact",
        "DisplayName": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"Contact","LanguageCode":1033}]},
        "Description": {"@odata.type":"Microsoft.Dynamics.CRM.Label","LocalizedLabels":[{"@odata.type":"Microsoft.Dynamics.CRM.LocalizedLabel","Label":"CRM Contact attending this meeting","LanguageCode":1033}]},
        "RequiredLevel": {"Value":"ApplicationRequired","CanBeChanged":true,"ManagedPropertyLogicalName":"canmodifyrequirementlevelsettings"}
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade", "Delete": "RemoveLink", "Merge": "NoCascade",
        "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"
    }
}')
check_error "$REL_MC_CON" "contact -> crad9_meetingcontact relationship"

# ---------------------------------------------------------------------------
# STEP 4: Add new entities to the solution
# ---------------------------------------------------------------------------
echo ""
log "=== STEP 4: Adding new entities to solution ==="

add_to_solution() {
    local entity="$1"
    local resp
    resp=$(dv_post "solutions(UniqueName='${SOLUTION_NAME}')/components" \
        "{\"ComponentId\": \"$(dv_get "EntityDefinitions(LogicalName='${entity}')" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('MetadataId',''))" 2>/dev/null)\",\"ComponentType\": 1,\"AddRequiredComponents\": false}")
    check_error "$resp" "Add ${entity} to solution"
}

add_to_solution "crad9_agendaitem"
add_to_solution "crad9_meetingcontact"

# ---------------------------------------------------------------------------
# STEP 5: Publish all customizations
# ---------------------------------------------------------------------------
echo ""
log "=== STEP 5: Publishing all customizations ==="
PUB_RESP=$(dv_post "PublishAllXml" '{}')
ok "Publish request sent"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "${GREEN}  Schema Provisioning Complete!${NC}"
echo "============================================="
echo ""
echo "  crad9_meeting (extended):"
echo "    + crad9_level           (Integer)"
echo "    + crad9_meetingstartdate (DateTime)"
echo "    + crad9_meetingenddate   (DateTime)"
echo "    + crad9_isuserallowedspfolder (Boolean)"
echo "    + crad9_spfoldercreated  (Boolean)"
echo ""
echo "  crad9_agendaitem (new table):"
echo "    + crad9_name (primary name)"
echo "    + crad9_meeting (lookup -> crad9_meeting)"
echo "    + crad9_sequence, crad9_description"
echo "    + crad9_spfolderpath, crad9_spfolderurl"
echo "    + crad9_foldercreated"
echo ""
echo "  crad9_meetingcontact (new table):"
echo "    + crad9_name (primary name)"
echo "    + crad9_meeting (lookup -> crad9_meeting)"
echo "    + crad9_contact (lookup -> contact)"
echo "    + crad9_role, crad9_rsvpstatus"
echo "    + crad9_spaccessgranted"
echo ""
echo "  Next: Run ./create_sharepoint_site.sh"
echo ""
