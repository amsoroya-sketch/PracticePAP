#!/usr/bin/env bash
# =============================================================================
# SharePoint Site Provisioner - Meeting Management
# Creates a new SharePoint site and Meetings document library using
# Microsoft Graph API (REST) with the existing app registration credentials.
#
# Site:    https://ABCTest179.sharepoint.com/sites/MeetingManagement
# Library: Meetings
# Folder structure per meeting: /Meetings/{MeetingName}/{AgendaItemName}/
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ---------------------------------------------------------------------------
# Load credentials from MSDev .env
# ---------------------------------------------------------------------------
ENV_FILE="/home/dev/Development/MSDev/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    error ".env file not found at $ENV_FILE"
fi

# Parse .env (skip comments and blank lines)
while IFS='=' read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    export "$key=$value"
done < "$ENV_FILE"

TENANT_ID="${SHAREPOINT_TENANT_ID}"
CLIENT_ID="${SHAREPOINT_CLIENT_ID}"
CLIENT_SECRET="${SHAREPOINT_CLIENT_SECRET}"
SP_ROOT_URL="${SHAREPOINT_URL}"   # https://ABCTest179.sharepoint.com

NEW_SITE_ALIAS="MeetingManagement"
NEW_SITE_TITLE="Meeting Management"
NEW_SITE_URL="${SP_ROOT_URL}/sites/${NEW_SITE_ALIAS}"
LIBRARY_NAME="Meetings"

echo ""
echo "============================================="
echo "  SharePoint Site Provisioner"
echo "  Target: ${NEW_SITE_URL}"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# Check dependencies
# ---------------------------------------------------------------------------
log "Checking dependencies..."
for cmd in curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        warn "$cmd not found - installing..."
        sudo apt-get update -q && sudo apt-get install -y "$cmd"
    fi
done
ok "Dependencies ready"

# ---------------------------------------------------------------------------
# 1. Get access token (Graph API)
# ---------------------------------------------------------------------------
log "Authenticating with Microsoft Graph API..."

TOKEN_URL="https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token"

TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials" \
    -d "client_id=${CLIENT_ID}" \
    -d "client_secret=${CLIENT_SECRET}" \
    -d "scope=https://graph.microsoft.com/.default")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty')

if [[ -z "$ACCESS_TOKEN" ]]; then
    echo "$TOKEN_RESPONSE" | jq .
    error "Failed to obtain access token. Check CLIENT_ID and CLIENT_SECRET."
fi

ok "Access token obtained"

# ---------------------------------------------------------------------------
# 2. Check if site already exists
# ---------------------------------------------------------------------------
log "Checking if site '${NEW_SITE_ALIAS}' already exists..."

SITE_CHECK=$(curl -s -X GET \
    "https://graph.microsoft.com/v1.0/sites/root:/sites/${NEW_SITE_ALIAS}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json")

SITE_ID=$(echo "$SITE_CHECK" | jq -r '.id // empty')

if [[ -n "$SITE_ID" ]]; then
    warn "Site already exists: ${NEW_SITE_URL}"
    warn "Site ID: ${SITE_ID}"
else
    # ---------------------------------------------------------------------------
    # 3. Create site via SharePoint REST API (Graph doesn't support site creation directly)
    #    Use the SharePoint Admin REST endpoint
    # ---------------------------------------------------------------------------
    log "Creating SharePoint site: ${NEW_SITE_URL} ..."

    # Get SharePoint-specific token
    SP_TOKEN_RESPONSE=$(curl -s -X POST "$TOKEN_URL" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials" \
        -d "client_id=${CLIENT_ID}" \
        -d "client_secret=${CLIENT_SECRET}" \
        -d "scope=${SP_ROOT_URL}/.default")

    SP_ACCESS_TOKEN=$(echo "$SP_TOKEN_RESPONSE" | jq -r '.access_token // empty')

    if [[ -z "$SP_ACCESS_TOKEN" ]]; then
        warn "Could not get SharePoint token - trying Graph approach..."
        SP_ACCESS_TOKEN="$ACCESS_TOKEN"
    fi

    ADMIN_URL="${SP_ROOT_URL%-my.sharepoint.com*}admin.sharepoint.com"
    TENANT_ADMIN_URL="https://$(echo "$SP_ROOT_URL" | sed 's|https://||' | cut -d'.' -f1)-admin.sharepoint.com"

    CREATE_RESPONSE=$(curl -s -X POST \
        "${SP_ROOT_URL}/_api/SPSiteManager/create" \
        -H "Authorization: Bearer ${SP_ACCESS_TOKEN}" \
        -H "Content-Type: application/json;odata.metadata=none" \
        -H "Accept: application/json;odata.metadata=none" \
        -d "{
            \"request\": {
                \"Title\": \"${NEW_SITE_TITLE}\",
                \"Url\": \"${NEW_SITE_URL}\",
                \"Lcid\": 1033,
                \"ShareByEmailEnabled\": false,
                \"Description\": \"Meeting Management - document repository for meeting agenda items\",
                \"WebTemplate\": \"STS#3\",
                \"SiteDesignId\": \"00000000-0000-0000-0000-000000000000\",
                \"Owner\": \"${CLIENT_ID}\"
            }
        }")

    SITE_STATUS=$(echo "$CREATE_RESPONSE" | jq -r '.SiteStatus // empty')
    SITE_URL_RESP=$(echo "$CREATE_RESPONSE" | jq -r '.SiteUrl // empty')

    if [[ "$SITE_STATUS" == "2" ]] || [[ -n "$SITE_URL_RESP" ]]; then
        ok "Site created: ${SITE_URL_RESP}"
    else
        warn "Site creation response:"
        echo "$CREATE_RESPONSE" | jq . 2>/dev/null || echo "$CREATE_RESPONSE"
        warn "Site may already exist or creation may be processing..."
        warn "Check: ${NEW_SITE_URL}"
    fi

    # Wait for provisioning
    log "Waiting 15 seconds for site to provision..."
    sleep 15

    # Re-fetch site ID
    SITE_CHECK=$(curl -s -X GET \
        "https://graph.microsoft.com/v1.0/sites/root:/sites/${NEW_SITE_ALIAS}" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")
    SITE_ID=$(echo "$SITE_CHECK" | jq -r '.id // empty')
fi

if [[ -z "$SITE_ID" ]]; then
    warn "Could not confirm site ID. Attempting to continue with known URL..."
    SITE_ID="root:/sites/${NEW_SITE_ALIAS}"
fi

ok "Site ID: ${SITE_ID}"

# ---------------------------------------------------------------------------
# 4. Create 'Meetings' document library
# ---------------------------------------------------------------------------
log "Creating '${LIBRARY_NAME}' document library..."

# Get existing drives (libraries)
DRIVES=$(curl -s -X GET \
    "https://graph.microsoft.com/v1.0/sites/${SITE_ID}/drives" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json")

EXISTING_DRIVE=$(echo "$DRIVES" | jq -r --arg name "$LIBRARY_NAME" \
    '.value[] | select(.name == $name) | .id // empty')

if [[ -n "$EXISTING_DRIVE" ]]; then
    warn "'${LIBRARY_NAME}' library already exists (Drive ID: ${EXISTING_DRIVE})"
    DRIVE_ID="$EXISTING_DRIVE"
else
    # Create library via SharePoint REST
    SP_TOKEN_RESPONSE2=$(curl -s -X POST "$TOKEN_URL" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials" \
        -d "client_id=${CLIENT_ID}" \
        -d "client_secret=${CLIENT_SECRET}" \
        -d "scope=${SP_ROOT_URL}/.default")

    SP_TOKEN2=$(echo "$SP_TOKEN_RESPONSE2" | jq -r '.access_token // empty')
    [[ -z "$SP_TOKEN2" ]] && SP_TOKEN2="$ACCESS_TOKEN"

    CREATE_LIB=$(curl -s -X POST \
        "${NEW_SITE_URL}/_api/web/lists" \
        -H "Authorization: Bearer ${SP_TOKEN2}" \
        -H "Content-Type: application/json;odata=verbose" \
        -H "Accept: application/json;odata=verbose" \
        -d "{
            \"__metadata\": { \"type\": \"SP.List\" },
            \"AllowContentTypes\": true,
            \"BaseTemplate\": 101,
            \"ContentTypesEnabled\": true,
            \"Description\": \"Meeting documents and agenda folders\",
            \"Title\": \"${LIBRARY_NAME}\"
        }")

    LIB_TITLE=$(echo "$CREATE_LIB" | jq -r '.d.Title // empty' 2>/dev/null)

    if [[ -n "$LIB_TITLE" ]]; then
        ok "Library '${LIB_TITLE}' created"
    else
        warn "Library creation response:"
        echo "$CREATE_LIB" | jq . 2>/dev/null || echo "$CREATE_LIB"
        warn "Library may already exist or permissions may be needed."
    fi

    # Re-fetch drive ID
    DRIVES2=$(curl -s -X GET \
        "https://graph.microsoft.com/v1.0/sites/${SITE_ID}/drives" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}")
    DRIVE_ID=$(echo "$DRIVES2" | jq -r --arg name "$LIBRARY_NAME" \
        '.value[] | select(.name == $name) | .id // empty')
fi

ok "Library drive ID: ${DRIVE_ID:-not yet available}"

# ---------------------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "${GREEN}  SharePoint Provisioning Complete!${NC}"
echo "============================================="
echo ""
echo "  Site URL    : ${NEW_SITE_URL}"
echo "  Library     : ${LIBRARY_NAME}"
echo "  Folder path : /sites/MeetingManagement/Meetings/{MeetingName}/{AgendaItemName}"
echo ""
echo "  Expected folder structure:"
echo "    Meetings/"
echo "    ├── Board Meeting 2026-02/"
echo "    │   ├── Agenda Item 1 - Budget Review/"
echo "    │   ├── Agenda Item 2 - Quarterly Report/"
echo "    │   └── Agenda Item 3 - HR Update/"
echo "    └── Team Sync 2026-03/"
echo "        ├── Agenda Item 1 - Project Status/"
echo "        └── Agenda Item 2 - Risks/"
echo ""
echo "  Power Automate flows will auto-create these folders"
echo "  when meetings are created in Dataverse."
echo ""
