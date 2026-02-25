#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install PowerShell (pwsh) if not already installed
if ! command -v pwsh &>/dev/null; then
  echo "Installing PowerShell..."

  # Add Microsoft package repository
  wget -q https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb -O /tmp/packages-microsoft-prod.deb
  dpkg -i /tmp/packages-microsoft-prod.deb
  rm /tmp/packages-microsoft-prod.deb

  apt-get update -q
  apt-get install -y powershell
  echo "PowerShell installed: $(pwsh --version)"
else
  echo "PowerShell already installed: $(pwsh --version)"
fi

# Create 'powershell' symlink so scripts that call 'powershell' work on Linux
if ! command -v powershell &>/dev/null; then
  ln -sf "$(command -v pwsh)" /usr/local/bin/powershell
  echo "Symlink created: powershell -> pwsh"
fi
