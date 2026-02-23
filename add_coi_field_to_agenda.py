#!/usr/bin/env python3
"""
Add Conflict of Interest field to Agenda Item table.

This script adds a boolean field 'crad9_hasconflictofinterest' to the
crad9_agendaitem table to track if any meeting member has declared a
conflict of interest on a specific agenda item.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from config import TENANT_ID, CLIENT_ID, CLIENT_SECRET, ORG_URL, API_URL

# Dataverse connection details (matching provision_dataverse_schema.py)

def get_access_token():
    """Get OAuth access token for Dataverse."""
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

def add_coi_field():
    """Add conflict of interest boolean field to agenda item table."""

    access_token = get_access_token()

    # Define the new field
    coi_field = {
        "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
        "AttributeType": "Boolean",
        "AttributeTypeName": {
            "Value": "BooleanType"
        },
        "SchemaName": "crad9_HasConflictOfInterest",
        "LogicalName": "crad9_hasconflictofinterest",
        "RequiredLevel": {
            "Value": "None",
            "CanBeChanged": True
        },
        "DisplayName": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "Has Conflict of Interest",
                    "LanguageCode": 1033
                }
            ]
        },
        "Description": {
            "@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [
                {
                    "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                    "Label": "Indicates if any meeting member has declared a conflict of interest on this agenda item",
                    "LanguageCode": 1033
                }
            ]
        },
        "DefaultValue": False,
        "OptionSet": {
            "@odata.type": "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata",
            "TrueOption": {
                "Value": 1,
                "Label": {
                    "@odata.type": "Microsoft.Dynamics.CRM.Label",
                    "LocalizedLabels": [
                        {
                            "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                            "Label": "Yes",
                            "LanguageCode": 1033
                        }
                    ]
                }
            },
            "FalseOption": {
                "Value": 0,
                "Label": {
                    "@odata.type": "Microsoft.Dynamics.CRM.Label",
                    "LocalizedLabels": [
                        {
                            "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                            "Label": "No",
                            "LanguageCode": 1033
                        }
                    ]
                }
            }
        }
    }

    # Add field to agenda item entity
    url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_agendaitem')/Attributes"

    print("=" * 80)
    print("ADDING CONFLICT OF INTEREST FIELD TO AGENDA ITEM TABLE")
    print("=" * 80)
    print()
    print(f"Entity: crad9_agendaitem")
    print(f"Field: crad9_hasconflictofinterest (Boolean)")
    print(f"Display Name: Has Conflict of Interest")
    print(f"Default Value: No (False)")
    print()

    try:
        data = json.dumps(coi_field).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("OData-MaxVersion", "4.0")
        req.add_header("OData-Version", "4.0")

        with urllib.request.urlopen(req) as resp:
            print("✓ Field added successfully!")
            print()
            print("Field details:")
            print("  - Logical Name: crad9_hasconflictofinterest")
            print("  - Schema Name: crad9_HasConflictOfInterest")
            print("  - Type: Boolean (Yes/No)")
            print("  - Required: No")
            print("  - Default: No")
            print()
            print("The field is now available on the Agenda Item form.")
            print("Users can check this box if any member has a conflict of interest.")
            return True

    except urllib.error.HTTPError as e:
        print(f"✗ Error adding field: HTTP {e.code}")
        print(f"Response: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"✗ Exception occurred: {str(e)}")
        return False

def verify_field():
    """Verify the field was added successfully."""

    access_token = get_access_token()
    url = f"{API_URL}/EntityDefinitions(LogicalName='crad9_agendaitem')/Attributes(LogicalName='crad9_hasconflictofinterest')"

    print()
    print("=" * 80)
    print("VERIFYING FIELD CREATION")
    print("=" * 80)
    print()

    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Accept", "application/json")
        req.add_header("OData-MaxVersion", "4.0")
        req.add_header("OData-Version", "4.0")

        with urllib.request.urlopen(req) as resp:
            field_data = json.loads(resp.read())
            print("✓ Field verified successfully!")
            print()
            print("Retrieved field metadata:")
            print(f"  - Display Name: {field_data.get('DisplayName', {}).get('UserLocalizedLabel', {}).get('Label', 'N/A')}")
            print(f"  - Logical Name: {field_data.get('LogicalName', 'N/A')}")
            print(f"  - Attribute Type: {field_data.get('AttributeTypeName', {}).get('Value', 'N/A')}")
            print(f"  - Required Level: {field_data.get('RequiredLevel', {}).get('Value', 'N/A')}")
            print()
            return True

    except urllib.error.HTTPError as e:
        print(f"✗ Field not found: HTTP {e.code}")
        return False
    except Exception as e:
        print(f"✗ Exception during verification: {str(e)}")
        return False

if __name__ == "__main__":
    print()
    print("🔧 CONFLICT OF INTEREST FIELD SETUP")
    print()

    # Add the field
    success = add_coi_field()

    if success:
        # Verify it was created
        verify_field()
        print()
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("1. The field is now available in Dataverse")
        print("2. Add it to the Agenda Item form via Power Apps form designer")
        print("3. Users can check this box when declaring conflicts")
        print("4. Consider adding a workflow to notify stakeholders when COI is declared")
        print()
    else:
        print()
        print("⚠️  Field creation failed. Please check the error messages above.")
        print()
