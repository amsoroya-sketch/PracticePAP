#!/usr/bin/env bash
# =============================================================================
# Import Power Automate Flows via Solution Import
#
# Imports the updated solution containing CreateMeetingSPFolder and
# CreateAgendaItemSPFolder workflows using PAC CLI
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

# =============================================================================
# Configuration
# =============================================================================

SOLUTION_ZIP="/home/dev/Development/PracticePAP/CRMPowerBISharePointIntegration_Updated.zip"
SETTINGS_FILE="/home/dev/Development/PracticePAP/deployment_settings.json"
ENV_URL="https://org3a2a4fe5.crm6.dynamics.com"

echo ""
echo "============================================="
echo "  Power Automate Flow Import via PAC CLI"
echo "============================================="
echo ""

# =============================================================================
# Step 1: Check PAC CLI installation
# =============================================================================

log "Checking PAC CLI installation..."

if ! command -v pac &>/dev/null; then
    warn "PAC CLI not found. Installing now..."

    # PAC CLI is already installed at ~/.pac-cli/ from earlier
    if [[ -f "$HOME/.local/bin/pac" ]]; then
        ok "PAC CLI found at ~/.local/bin/pac"
    else
        error "PAC CLI not installed. Run install_pac_cli.sh first."
    fi
else
    ok "PAC CLI installed"
fi

# Get version
PAC_VERSION=$(pac help 2>&1 | head -n 1 || echo "unknown")
log "Version: $PAC_VERSION"

# =============================================================================
# Step 2: Authenticate to environment
# =============================================================================

log "Checking authentication to ${ENV_URL}..."

# Check if already authenticated
AUTH_LIST=$(pac auth list 2>&1 || echo "")

if echo "$AUTH_LIST" | grep -q "$ENV_URL"; then
    ok "Already authenticated to environment"
else
    warn "Not authenticated. Please authenticate manually:"
    echo ""
    echo "  Run this command:"
    echo "  pac auth create --url ${ENV_URL}"
    echo ""
    read -p "Press ENTER after authenticating..."
fi

# =============================================================================
# Step 3: Generate deployment settings (if not exists)
# =============================================================================

if [[ ! -f "$SETTINGS_FILE" ]]; then
    log "Generating deployment settings file..."

    pac solution create-settings \
        --solution-zip "$SOLUTION_ZIP" \
        --settings-file "$SETTINGS_FILE" 2>&1 || warn "Settings generation may have issues"

    if [[ -f "$SETTINGS_FILE" ]]; then
        ok "Settings file created: $SETTINGS_FILE"
        warn "You MUST edit this file to configure connection references!"
        warn "See instructions below."
    else
        warn "Could not generate settings file automatically"
        warn "Proceeding with import (connections will need manual configuration)"
    fi
else
    ok "Deployment settings file already exists: $SETTINGS_FILE"
fi

# =============================================================================
# Step 4: Display connection reference instructions
# =============================================================================

echo ""
echo "============================================="
echo "  IMPORTANT: Connection Reference Setup"
echo "============================================="
echo ""
echo "  The solution contains 2 connection references:"
echo "    1. shared_commondataserviceforapps (Dataverse)"
echo "    2. shared_sharepointonline (SharePoint Online)"
echo ""
echo "  BEFORE importing, you must:"
echo ""
echo "  Option A: Manual Connection Creation (RECOMMENDED for first-time)"
echo "  ----------------------------------------------------------------"
echo "  1. Go to: https://make.powerapps.com"
echo "  2. Select your environment"
echo "  3. Go to: Data > Connections"
echo "  4. Create connections:"
echo "     • Microsoft Dataverse"
echo "     • SharePoint Online"
echo "  5. Note the connection IDs (you'll see them in URLs)"
echo ""
echo "  Option B: Use Default Connections (if they exist)"
echo "  -------------------------------------------------"
echo "  1. Skip manual creation"
echo "  2. Import solution without settings file"
echo "  3. Configure connections in Power Automate after import"
echo ""

read -p "Have you created the connections? (y/N): " CONNECTIONS_READY

if [[ "$CONNECTIONS_READY" != "y" && "$CONNECTIONS_READY" != "Y" ]]; then
    warn "Connections not ready. Import will proceed but flows will be OFF."
    warn "You'll need to configure connections manually after import."
    echo ""
    read -p "Continue anyway? (y/N): " CONTINUE

    if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
        error "Import cancelled. Create connections first."
    fi
fi

# =============================================================================
# Step 5: Import solution
# =============================================================================

echo ""
echo "============================================="
echo "  Importing Solution with Flows"
echo "============================================="
echo ""

log "Importing solution: CRMPowerBISharePointIntegration v1.0.0.8..."

# Import command
IMPORT_ARGS=(
    solution import
    --path "$SOLUTION_ZIP"
    --publish-changes
)

# Add settings file if it exists and was configured
if [[ -f "$SETTINGS_FILE" ]]; then
    log "Using deployment settings: $SETTINGS_FILE"
    IMPORT_ARGS+=(--settings-file "$SETTINGS_FILE")
fi

# Run import
pac "${IMPORT_ARGS[@]}" 2>&1 || {
    error "Solution import failed. Check connection references and try again."
}

ok "Solution import completed!"

# =============================================================================
# Step 6: Verify import
# =============================================================================

log "Verifying solution import..."

# List solutions
SOLUTION_CHECK=$(pac solution list 2>&1 || echo "")

if echo "$SOLUTION_CHECK" | grep -q "CRMPowerBISharePointIntegration"; then
    ok "Solution found in environment"
else
    warn "Could not verify solution import via PAC CLI"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "============================================="
echo "  Import Complete!"
echo "============================================="
echo ""
echo "  Solution: CRMPowerBISharePointIntegration v1.0.0.8"
echo "  Flows Imported:"
echo "    • CreateMeetingSPFolder"
echo "    • CreateAgendaItemSPFolder"
echo ""
echo "  NEXT STEPS:"
echo ""
echo "  1. Go to: https://make.powerautomate.com"
echo "  2. Select your environment"
echo "  3. Find the imported flows (they will be OFF)"
echo "  4. For each flow:"
echo "     a. Open the flow"
echo "     b. Check connection references (Fix if needed)"
echo "     c. Turn ON the flow"
echo ""
echo "  5. Test the flows:"
echo "     - Update an existing meeting to set:"
echo "       • Is User Allowed SP Folder = Yes"
echo "       • SP Folder Created = No"
echo "     - Verify CreateMeetingSPFolder triggers"
echo "     - Create an agenda item"
echo "     - Verify CreateAgendaItemSPFolder triggers"
echo ""
echo "  6. Run: python3 check_flow_import_status.py"
echo "     to verify flow import programmatically"
echo ""
echo "  7. Run: python3 test_workflow_execution.py"
echo "     to test end-to-end workflow execution"
echo ""
