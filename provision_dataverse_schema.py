#!/usr/bin/env python3
"""
Dataverse Schema Provisioner - Meeting Management
Creates new columns and tables via Dataverse Web API directly.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

SOLUTION_NAME = "CRMPowerBISharePointIntegration"


def get_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": f"{ORG_URL}/.default"
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def api_call(method, path, payload=None, token=None):
    url = f"{API_URL}/{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("OData-MaxVersion", "4.0")
    req.add_header("OData-Version", "4.0")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return json.loads(body) if body else {"ok": True}
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return json.loads(body)
        except Exception:
            return {"error": {"message": str(e)}}


def check(resp, label):
    if "error" in resp:
        msg = resp["error"].get("message", "unknown")
        skip_keywords = ["already exists", "duplicate", "already defined",
                         "An attribute with the specified name", "entity already exists",
                         "A component with the specified Id"]
        if any(k.lower() in msg.lower() for k in skip_keywords):
            print(f"  [SKIP] {label} (already exists)")
        else:
            print(f"  [WARN] {label}: {msg[:200]}")
    else:
        print(f"  [OK]   {label}")


def label(text, lang=1033):
    return {"@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                                  "Label": text, "LanguageCode": lang}]}


def req_level(val="None"):
    return {"Value": val, "CanBeChanged": True,
            "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"}


def bool_attr(schema, logical, display, description):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
        "SchemaName": schema, "LogicalName": logical,
        "DisplayName": label(display), "Description": label(description),
        "RequiredLevel": req_level("None"), "DefaultValue": False,
        "OptionSet": {
            "TrueOption": {"Value": 1, "Label": label("Yes")},
            "FalseOption": {"Value": 0, "Label": label("No")}
        }
    }


print("\n=============================================")
print("  Dataverse Schema Provisioner")
print(f"  Org: {ORG_URL}")
print("=============================================\n")

print("Getting access token...")
TOKEN = get_token()
print(f"Token: {TOKEN[:15]}...\n")


# ─── STEP 1: Add columns to crad9_meeting ────────────────────────────────────
print("=== STEP 1: Extending crad9_meeting ===\n")

cols = [
    {
        "@odata.type": "Microsoft.Dynamics.CRM.IntegerAttributeMetadata",
        "SchemaName": "crad9_Level", "LogicalName": "crad9_level",
        "DisplayName": label("Level"),
        "Description": label("Hierarchy level of the meeting"),
        "RequiredLevel": req_level(),
        "MinValue": 0, "MaxValue": 2147483647, "Format": "None"
    },
    {
        "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
        "SchemaName": "crad9_MeetingStartDate", "LogicalName": "crad9_meetingstartdate",
        "DisplayName": label("Meeting Start Date"),
        "Description": label("Date and time when the meeting starts"),
        "RequiredLevel": req_level(),
        "Format": "DateAndTime", "DateTimeBehavior": {"Value": "UserLocal"}
    },
    {
        "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
        "SchemaName": "crad9_MeetingEndDate", "LogicalName": "crad9_meetingenddate",
        "DisplayName": label("Meeting End Date"),
        "Description": label("Date and time when the meeting ends"),
        "RequiredLevel": req_level(),
        "Format": "DateAndTime", "DateTimeBehavior": {"Value": "UserLocal"}
    },
    bool_attr("crad9_IsUserAllowedSPFolder", "crad9_isuserallowedspfolder",
              "Is User Allowed SharePoint Folder",
              "Indicates whether the user is allowed to access the SharePoint folder"),
    bool_attr("crad9_SPFolderCreated", "crad9_spfoldercreated",
              "SP Folder Created",
              "Indicates whether the SharePoint folder has been provisioned"),
]

for col in cols:
    r = api_call("POST", "EntityDefinitions(LogicalName='crad9_meeting')/Attributes", col, TOKEN)
    check(r, col["LogicalName"])


# ─── STEP 2: Create crad9_agendaitem ─────────────────────────────────────────
print("\n=== STEP 2: Creating crad9_agendaitem table ===\n")

agenda_entity = {
    "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
    "SchemaName": "crad9_AgendaItem", "LogicalName": "crad9_agendaitem",
    "DisplayName": label("Agenda Item"),
    "DisplayCollectionName": label("Agenda Items"),
    "Description": label("Agenda items for a meeting, each mapped to a SharePoint folder"),
    "OwnershipType": "UserOwned",
    "IsActivity": False, "HasActivities": False, "HasNotes": False,
    "PrimaryNameAttribute": "crad9_name",
    "Attributes": [{
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
        "SchemaName": "crad9_name", "LogicalName": "crad9_name",
        "IsPrimaryName": True,
        "DisplayName": label("Agenda Item Name"),
        "RequiredLevel": req_level("ApplicationRequired"),
        "MaxLength": 200, "Format": "Text"
    }]
}

r = api_call("POST", "EntityDefinitions", agenda_entity, TOKEN)
check(r, "crad9_agendaitem table")

print("  Waiting 8s for entity to provision...")
time.sleep(8)

agenda_cols = [
    {
        "@odata.type": "Microsoft.Dynamics.CRM.IntegerAttributeMetadata",
        "SchemaName": "crad9_Sequence", "LogicalName": "crad9_sequence",
        "DisplayName": label("Order / Sequence"),
        "Description": label("Display order of the agenda item within the meeting"),
        "RequiredLevel": req_level(),
        "MinValue": 0, "MaxValue": 2147483647, "Format": "None"
    },
    {
        "@odata.type": "Microsoft.Dynamics.CRM.MemoAttributeMetadata",
        "SchemaName": "crad9_Description", "LogicalName": "crad9_description",
        "DisplayName": label("Description"),
        "Description": label("Detailed description of the agenda item"),
        "RequiredLevel": req_level(),
        "MaxLength": 4000, "Format": "Text"
    },
    {
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
        "SchemaName": "crad9_SPFolderPath", "LogicalName": "crad9_spfolderpath",
        "DisplayName": label("SharePoint Folder Path"),
        "Description": label("Relative path of the SharePoint folder for this agenda item"),
        "RequiredLevel": req_level(),
        "MaxLength": 500, "Format": "Text"
    },
    {
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
        "SchemaName": "crad9_SPFolderURL", "LogicalName": "crad9_spfolderurl",
        "DisplayName": label("SharePoint Folder URL"),
        "Description": label("Direct URL to the SharePoint folder for this agenda item"),
        "RequiredLevel": req_level(),
        "MaxLength": 500, "Format": "Url"
    },
    bool_attr("crad9_FolderCreated", "crad9_foldercreated",
              "Folder Created",
              "Indicates whether the SharePoint folder has been auto-created"),
]

for col in agenda_cols:
    r = api_call("POST", "EntityDefinitions(LogicalName='crad9_agendaitem')/Attributes", col, TOKEN)
    check(r, f"crad9_agendaitem.{col['LogicalName']}")

# Meeting → AgendaItem relationship
print("\n  Creating Meeting → AgendaItem lookup relationship...")
r = api_call("POST", "RelationshipDefinitions", {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_meeting_crad9_agendaitem",
    "ReferencedEntity": "crad9_meeting",
    "ReferencingEntity": "crad9_agendaitem",
    "ReferencedAttribute": "crad9_meetingid",
    "ReferencingAttribute": "crad9_meeting",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Meeting", "LogicalName": "crad9_meeting",
        "DisplayName": label("Meeting"),
        "Description": label("Parent meeting this agenda item belongs to"),
        "RequiredLevel": req_level("ApplicationRequired")
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade", "Delete": "RemoveLink", "Merge": "NoCascade",
        "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"
    }
}, TOKEN)
check(r, "crad9_meeting -> crad9_agendaitem relationship")


# ─── STEP 3: Create crad9_meetingcontact ─────────────────────────────────────
print("\n=== STEP 3: Creating crad9_meetingcontact table ===\n")

mc_entity = {
    "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
    "SchemaName": "crad9_MeetingContact", "LogicalName": "crad9_meetingcontact",
    "DisplayName": label("Meeting Contact"),
    "DisplayCollectionName": label("Meeting Contacts"),
    "Description": label("Junction table linking contacts to meetings with attendance details"),
    "OwnershipType": "UserOwned",
    "IsActivity": False, "HasActivities": False, "HasNotes": False,
    "PrimaryNameAttribute": "crad9_name",
    "Attributes": [{
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
        "SchemaName": "crad9_name", "LogicalName": "crad9_name",
        "IsPrimaryName": True,
        "DisplayName": label("Name"),
        "RequiredLevel": req_level("None"),
        "MaxLength": 200, "Format": "Text"
    }]
}

r = api_call("POST", "EntityDefinitions", mc_entity, TOKEN)
check(r, "crad9_meetingcontact table")

print("  Waiting 8s for entity to provision...")
time.sleep(8)

def picklist_attr(schema, logical, display, description, options):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
        "SchemaName": schema, "LogicalName": logical,
        "DisplayName": label(display), "Description": label(description),
        "RequiredLevel": req_level(),
        "OptionSet": {
            "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
            "IsGlobal": False, "OptionSetType": "Picklist",
            "Options": [
                {"Value": v, "Label": label(l)} for v, l in options
            ]
        }
    }


mc_cols = [
    picklist_attr("crad9_Role", "crad9_role", "Role",
                  "Role of this contact in the meeting",
                  [(117160000, "Organizer"), (117160001, "Attendee"), (117160002, "Optional")]),
    picklist_attr("crad9_RSVPStatus", "crad9_rsvpstatus", "RSVP Status",
                  "Attendance confirmation status for this contact",
                  [(117160000, "Pending"), (117160001, "Accepted"),
                   (117160002, "Declined"), (117160003, "Tentative")]),
    bool_attr("crad9_SPAccessGranted", "crad9_spaccessgranted",
              "SP Access Granted",
              "Indicates whether this contact has been granted SharePoint folder access"),
]

for col in mc_cols:
    r = api_call("POST", "EntityDefinitions(LogicalName='crad9_meetingcontact')/Attributes", col, TOKEN)
    check(r, f"crad9_meetingcontact.{col['LogicalName']}")

# Meeting → MeetingContact
print("\n  Creating Meeting → MeetingContact relationship...")
r = api_call("POST", "RelationshipDefinitions", {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "crad9_meeting_crad9_meetingcontact",
    "ReferencedEntity": "crad9_meeting",
    "ReferencingEntity": "crad9_meetingcontact",
    "ReferencedAttribute": "crad9_meetingid",
    "ReferencingAttribute": "crad9_meeting",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Meeting", "LogicalName": "crad9_meeting",
        "DisplayName": label("Meeting"),
        "Description": label("Meeting this contact is linked to"),
        "RequiredLevel": req_level("ApplicationRequired")
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade", "Delete": "RemoveLink", "Merge": "NoCascade",
        "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"
    }
}, TOKEN)
check(r, "crad9_meeting -> crad9_meetingcontact relationship")

# Contact → MeetingContact
print("  Creating Contact → MeetingContact relationship...")
r = api_call("POST", "RelationshipDefinitions", {
    "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
    "SchemaName": "contact_crad9_meetingcontact",
    "ReferencedEntity": "contact",
    "ReferencingEntity": "crad9_meetingcontact",
    "ReferencedAttribute": "contactid",
    "ReferencingAttribute": "crad9_contact",
    "Lookup": {
        "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
        "SchemaName": "crad9_Contact", "LogicalName": "crad9_contact",
        "DisplayName": label("Contact"),
        "Description": label("CRM Contact attending this meeting"),
        "RequiredLevel": req_level("ApplicationRequired")
    },
    "CascadeConfiguration": {
        "Assign": "NoCascade", "Delete": "RemoveLink", "Merge": "NoCascade",
        "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"
    }
}, TOKEN)
check(r, "contact -> crad9_meetingcontact relationship")


# ─── STEP 4: Publish all customizations ──────────────────────────────────────
print("\n=== STEP 4: Publishing all customizations ===\n")
r = api_call("POST", "PublishAllXml", {}, TOKEN)
print("  Publish request sent")

print("\n=============================================")
print("  Provisioning Complete!")
print("=============================================")
print("""
  crad9_meeting (extended):
    + crad9_level             (Integer)
    + crad9_meetingstartdate  (DateTime)
    + crad9_meetingenddate    (DateTime)
    + crad9_isuserallowedspfolder (Boolean)
    + crad9_spfoldercreated   (Boolean)

  crad9_agendaitem (new):
    + crad9_name (primary name, required)
    + crad9_meeting (lookup -> crad9_meeting, required)
    + crad9_sequence, crad9_description
    + crad9_spfolderpath, crad9_spfolderurl
    + crad9_foldercreated

  crad9_meetingcontact (new):
    + crad9_name (primary name)
    + crad9_meeting (lookup -> crad9_meeting, required)
    + crad9_contact (lookup -> contact, required)
    + crad9_role, crad9_rsvpstatus
    + crad9_spaccessgranted

  Next: Run ./create_sharepoint_site.sh
""")
