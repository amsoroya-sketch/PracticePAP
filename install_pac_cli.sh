#!/usr/bin/env bash
# =============================================================================
# PAC CLI Installer for Ubuntu
# Installs Microsoft Power Apps CLI (pac) via manual NuGet extraction
#
# WHY MANUAL: The NuGet package targets net10.0. dotnet tool install fails
# if .NET 10 is not installed. This script installs .NET 10 if needed,
# then extracts pac.dll directly from the NuGet package and creates a
# wrapper script so 'pac' works from any terminal.
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()   { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

PAC_VERSION="2.2.1"
PAC_INSTALL_DIR="$HOME/.pac-cli"
PAC_BIN="$HOME/.local/bin/pac"
NUPKG_URL="https://www.nuget.org/api/v2/package/microsoft.powerapps.cli.tool/${PAC_VERSION}"

echo ""
echo "============================================="
echo "  PAC CLI Installer - Power Platform (Ubuntu)"
echo "  Package: microsoft.powerapps.cli.tool v${PAC_VERSION}"
echo "============================================="
echo ""

# -----------------------------------------------------------------------------
# 1. Check dependencies
# -----------------------------------------------------------------------------
log "Checking dependencies..."

for cmd in curl unzip dotnet; do
    if ! command -v "$cmd" &>/dev/null; then
        warn "$cmd not found - installing..."
        sudo apt-get update -q && sudo apt-get install -y "$cmd"
    fi
done

# -----------------------------------------------------------------------------
# 2. Check .NET 10 (required by pac's net10.0 target)
# -----------------------------------------------------------------------------
log "Checking .NET 10 runtime..."

DOTNET_10_INSTALLED=false
if dotnet --list-runtimes 2>/dev/null | grep -q "Microsoft.NETCore.App 10\."; then
    DOTNET_10_INSTALLED=true
    ok ".NET 10 runtime already installed"
fi

if [[ "$DOTNET_10_INSTALLED" == "false" ]]; then
    log ".NET 10 not found. Installing .NET 10 SDK..."

    # Add Microsoft package feed if not already present
    UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "24.04")
    FEED_PKG="/tmp/packages-microsoft-prod.deb"

    if [[ ! -f /etc/apt/sources.list.d/microsoft-prod.list ]] && \
       ! apt-cache policy 2>/dev/null | grep -q "packages.microsoft.com"; then
        log "Adding Microsoft package feed for Ubuntu ${UBUNTU_VERSION}..."
        curl -sL "https://packages.microsoft.com/config/ubuntu/${UBUNTU_VERSION}/packages-microsoft-prod.deb" \
            -o "$FEED_PKG"
        sudo dpkg -i "$FEED_PKG"
        rm -f "$FEED_PKG"
        sudo apt-get update -q
    fi

    # Install .NET 10 SDK
    sudo apt-get install -y dotnet-sdk-10.0 || {
        warn "dotnet-sdk-10.0 not yet in apt. Trying dotnet-sdk-10 (preview)..."
        sudo apt-get install -y dotnet-sdk-10 || {
            # Fallback: install via official script
            log "Falling back to dotnet-install.sh script..."
            curl -sL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
            chmod +x /tmp/dotnet-install.sh
            /tmp/dotnet-install.sh --channel 10.0 --install-dir "$HOME/.dotnet"
            export PATH="$PATH:$HOME/.dotnet"
            echo 'export PATH="$PATH:$HOME/.dotnet"' >> "$HOME/.bashrc"
        }
    }

    # Verify
    if dotnet --list-runtimes 2>/dev/null | grep -q "Microsoft.NETCore.App 10\."; then
        ok ".NET 10 installed successfully"
    else
        error ".NET 10 installation failed. Check https://dot.net/v1/dotnet-install.sh manually."
    fi
fi

DOTNET_VERSION=$(dotnet --version 2>/dev/null || echo "unknown")
ok "Active dotnet version: $DOTNET_VERSION"

# -----------------------------------------------------------------------------
# 3. Download NuGet package
# -----------------------------------------------------------------------------
NUPKG_CACHE="/tmp/pac-cli-${PAC_VERSION}.nupkg"

if [[ -f "$NUPKG_CACHE" ]]; then
    log "Using cached nupkg: $NUPKG_CACHE"
else
    log "Downloading PAC CLI v${PAC_VERSION} from NuGet (~75MB)..."
    curl -L "$NUPKG_URL" -o "$NUPKG_CACHE" --progress-bar
fi

ok "Download complete: $(du -h "$NUPKG_CACHE" | cut -f1)"

# -----------------------------------------------------------------------------
# 4. Extract to install directory
# -----------------------------------------------------------------------------
log "Extracting to $PAC_INSTALL_DIR ..."

rm -rf "$PAC_INSTALL_DIR"
mkdir -p "$PAC_INSTALL_DIR"
unzip -q "$NUPKG_CACHE" "tools/net10.0/any/*" -d "$PAC_INSTALL_DIR"

PAC_DLL="$PAC_INSTALL_DIR/tools/net10.0/any/pac.dll"

if [[ ! -f "$PAC_DLL" ]]; then
    error "pac.dll not found after extraction. Expected: $PAC_DLL"
fi

ok "Extracted pac.dll"

# -----------------------------------------------------------------------------
# 5. Create wrapper script
# -----------------------------------------------------------------------------
log "Creating 'pac' wrapper at $PAC_BIN ..."

mkdir -p "$(dirname "$PAC_BIN")"

cat > "$PAC_BIN" <<EOF
#!/usr/bin/env bash
# PAC CLI wrapper - installed by install_pac_cli.sh
exec dotnet "$PAC_DLL" "\$@"
EOF

chmod +x "$PAC_BIN"
ok "Wrapper created: $PAC_BIN"

# -----------------------------------------------------------------------------
# 6. Ensure ~/.local/bin is on PATH
# -----------------------------------------------------------------------------
LOCAL_BIN="$HOME/.local/bin"
SHELL_RC=""

if [[ "$SHELL" == */zsh ]]; then
    SHELL_RC="$HOME/.zshrc"
else
    SHELL_RC="$HOME/.bashrc"
fi

if ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
    log "Adding $LOCAL_BIN to PATH in $SHELL_RC..."
    {
        echo ""
        echo "# PAC CLI (Power Platform)"
        echo "export PATH=\"\$PATH:$LOCAL_BIN\""
    } >> "$SHELL_RC"
    ok "PATH updated in $SHELL_RC"
else
    ok "$LOCAL_BIN already in PATH"
fi

export PATH="$PATH:$LOCAL_BIN"

# -----------------------------------------------------------------------------
# 7. Verify
# -----------------------------------------------------------------------------
log "Verifying installation..."

if ! command -v pac &>/dev/null; then
    error "'pac' not found. Try: source $SHELL_RC && pac --version"
fi

PAC_VER_OUT=$(pac --version 2>&1 || true)
ok "PAC CLI working: $PAC_VER_OUT"

# -----------------------------------------------------------------------------
# 8. Summary
# -----------------------------------------------------------------------------
echo ""
echo "============================================="
echo -e "${GREEN}  Installation Complete!${NC}"
echo "============================================="
echo ""
echo "  pac version : $PAC_VER_OUT"
echo "  pac binary  : $PAC_BIN"
echo "  pac dll     : $PAC_DLL"
echo ""
echo "  Authenticate (browser - interactive):"
echo "    pac auth create --environment https://org3a2a4fe5.crm6.dynamics.com"
echo ""
echo "  Authenticate (service principal):"
echo "    pac auth create \\"
echo "      --environment https://org3a2a4fe5.crm6.dynamics.com \\"
echo "      --applicationId <CLIENT_ID> \\"
echo "      --clientSecret <CLIENT_SECRET> \\"
echo "      --tenant <TENANT_ID>"
echo ""
echo "  Useful commands:"
echo "    pac org list              # list environments"
echo "    pac solution list         # list solutions"
echo "    pac solution export --name MySolution --path ./export"
echo ""
echo "  NOTE: If 'pac' is not found in a new terminal, run:"
echo "    source $SHELL_RC"
echo ""
