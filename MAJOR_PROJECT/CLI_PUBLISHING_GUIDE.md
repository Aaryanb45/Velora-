# Velora CLI - Complete Publishing & Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for publishing and deploying the Velora CLI tool across multiple platforms, making it accessible to clients via various installation methods.

## 🏗️ Current Build Status

✅ **CLI Implementation**: Complete with all commands
✅ **Cross-platform Binaries**: Linux, macOS, Windows
✅ **Package Configuration**: Ready for distribution
✅ **Installation Scripts**: Automated installers created

## 📦 Distribution Channels

### 1. NPM Registry (Recommended)

**Preparation:**
```bash
# Navigate to CLI directory
cd /app/MAJOR_PROJECT/cli

# Update package.json version
npm version patch  # or minor/major

# Login to npm (one-time setup)
npm login

# Publish to npm registry
npm publish
```

**User Installation:**
```bash
# Global installation
npm install -g velora-cli

# Direct usage
npx velora-cli
```

### 2. GitHub Releases (Binary Distribution)

**Setup GitHub Release:**
```bash
# Build all platform binaries
./scripts/build-release.sh

# Create GitHub release (manually or via GitHub CLI)
gh release create v1.0.0 \
  dist/velora-cli-linux \
  dist/velora-cli-macos \
  dist/velora-cli-win.exe \
  dist/SHA256SUMS \
  --title "Velora CLI v1.0.0" \
  --notes "Initial release of Velora CLI"
```

**User Installation:**
```bash
# Linux
curl -L -o velora https://github.com/velora/cli/releases/latest/download/velora-cli-linux
chmod +x velora && sudo mv velora /usr/local/bin/

# macOS
curl -L -o velora https://github.com/velora/cli/releases/latest/download/velora-cli-macos
chmod +x velora && sudo mv velora /usr/local/bin/

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/velora/cli/releases/latest/download/velora-cli-win.exe" -OutFile "velora.exe"
```

### 3. Homebrew (macOS/Linux)

**Create Homebrew Tap:**
```bash
# Create tap repository
mkdir homebrew-velora
cd homebrew-velora

# Add formula (already generated in dist/homebrew/)
cp ../dist/homebrew/velora-cli.rb ./Formula/

# Push to GitHub as homebrew-velora repository
git init && git add . && git commit -m "Add Velora CLI formula"
git remote add origin https://github.com/your-org/homebrew-velora.git
git push -u origin main
```

**User Installation:**
```bash
# Add tap and install
brew tap your-org/velora
brew install velora-cli

# Or direct install
brew install your-org/velora/velora-cli
```

### 4. Curl Installer (Universal)

**Host installer script:**
```bash
# Upload dist/installers/install.sh to https://get.velora.dev
# Ensure it's accessible via HTTPS
```

**User Installation:**
```bash
# Unix systems (Linux/macOS)
curl -fsSL https://get.velora.dev | sh

# Alternative with explicit bash
curl -fsSL https://get.velora.dev | bash
```

### 5. Windows PowerShell Installer

**Host PowerShell script:**
```bash
# Upload dist/installers/install.ps1 to https://get.velora.dev/install.ps1
```

**User Installation:**
```powershell
# Windows PowerShell
iwr -useb https://get.velora.dev/install.ps1 | iex

# Or download and run
Invoke-WebRequest -Uri "https://get.velora.dev/install.ps1" -OutFile "install.ps1"
.\install.ps1
```

## 🔧 Platform-Specific Deployment

### Linux Deployment
```bash
# Debian/Ubuntu package (advanced)
# 1. Create .deb package structure
mkdir -p velora-cli_1.0.0/DEBIAN
mkdir -p velora-cli_1.0.0/usr/local/bin

# 2. Add control file
cat > velora-cli_1.0.0/DEBIAN/control << EOF
Package: velora-cli
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Velora Team <support@velora.dev>
Description: Velora CLI - Cloud-Native Internal Developer Platform
EOF

# 3. Copy binary and build package
cp dist/velora-cli-linux velora-cli_1.0.0/usr/local/bin/velora
dpkg-deb --build velora-cli_1.0.0

# 4. Users can install with:
# sudo dpkg -i velora-cli_1.0.0.deb
```

### macOS Deployment
```bash
# Create macOS app bundle (optional)
mkdir -p VeloraCLI.app/Contents/MacOS
cp dist/velora-cli-macos VeloraCLI.app/Contents/MacOS/velora

# Create Info.plist
cat > VeloraCLI.app/Contents/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>velora</string>
    <key>CFBundleIdentifier</key>
    <string>dev.velora.cli</string>
    <key>CFBundleName</key>
    <string>Velora CLI</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
</dict>
</plist>
EOF
```

### Windows Deployment
```bash
# Create Windows installer with NSIS (advanced)
# 1. Install NSIS
# 2. Create installer script
cat > velora-installer.nsi << 'EOF'
!define APP_NAME "Velora CLI"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Velora Team"

Name "${APP_NAME}"
OutFile "velora-cli-installer.exe"
InstallDir "$PROGRAMFILES\Velora"

Section "Main"
    SetOutPath "$INSTDIR"
    File "dist\velora-cli-win.exe"
    
    # Add to PATH
    EnVar::AddValue "PATH" "$INSTDIR"
    
    # Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd
EOF

# 3. Build installer
# makensis velora-installer.nsi
```

## 🌐 CDN Distribution (Advanced)

### Setup CDN for Fast Downloads
```bash
# Upload binaries to CDN (AWS CloudFront, Cloudflare, etc.)
# Structure:
# https://cdn.velora.dev/cli/v1.0.0/linux/velora
# https://cdn.velora.dev/cli/v1.0.0/macos/velora
# https://cdn.velora.dev/cli/v1.0.0/windows/velora.exe
# https://cdn.velora.dev/cli/latest/linux/velora (symlink)

# Update installer scripts to use CDN URLs
sed -i 's|github.com/velora/cli/releases|cdn.velora.dev/cli|g' dist/installers/install.sh
```

## 📊 Usage Analytics (Optional)

### Track CLI Usage
```javascript
// Add to src/api/client.js
const packageJson = require('../package.json');

class ApiClient {
  async trackUsage(command) {
    try {
      await this.client.post('/cli/analytics', {
        version: packageJson.version,
        command: command,
        platform: process.platform,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      // Silently fail - don't break CLI for analytics
    }
  }
}
```

## 🧪 Testing Distribution

### Test All Installation Methods
```bash
# Test npm installation
npm install -g velora-cli
velora --version

# Test binary download
curl -L -o velora https://github.com/velora/cli/releases/latest/download/velora-cli-linux
chmod +x velora && ./velora --version

# Test curl installer
curl -fsSL https://get.velora.dev | sh

# Test Homebrew
brew install your-org/velora/velora-cli
```

### Automated Testing
```bash
# Create test script
cat > test-installations.sh << 'EOF'
#!/bin/bash
set -e

echo "🧪 Testing all installation methods..."

# Test NPM
if command -v npm >/dev/null 2>&1; then
    echo "Testing NPM installation..."
    npm install -g velora-cli
    velora --version
    npm uninstall -g velora-cli
fi

# Test binary
echo "Testing binary installation..."
curl -L -o /tmp/velora https://github.com/velora/cli/releases/latest/download/velora-cli-linux
chmod +x /tmp/velora
/tmp/velora --version
rm /tmp/velora

echo "✅ All tests passed!"
EOF

chmod +x test-installations.sh && ./test-installations.sh
```

## 🚀 Deployment Checklist

### Pre-Release
- [ ] All CLI commands tested and working
- [ ] Cross-platform binaries built successfully
- [ ] Installation scripts created and tested
- [ ] Documentation updated
- [ ] Version numbers consistent across all files

### Release Process
- [ ] Create GitHub release with binaries
- [ ] Publish to NPM registry
- [ ] Update installer script URLs
- [ ] Submit Homebrew formula (if creating tap)
- [ ] Test all installation methods
- [ ] Update documentation with installation instructions

### Post-Release
- [ ] Monitor installation analytics
- [ ] Respond to user issues
- [ ] Update download counts/metrics
- [ ] Plan next release cycle

## 📚 User Documentation

### Installation Instructions for Users

**Quick Install (Recommended):**
```bash
# Unix (Linux/macOS)
curl -fsSL https://get.velora.dev | sh

# Windows (PowerShell)
iwr -useb https://get.velora.dev/install.ps1 | iex

# NPM
npm install -g velora-cli

# Homebrew
brew install your-org/velora/velora-cli
```

**Manual Installation:**
- Download binaries from [GitHub Releases](https://github.com/velora/cli/releases)
- Extract and move to PATH
- Make executable (Unix systems)

**Getting Started:**
```bash
# Configure CLI
velora config setup

# Create first service
velora create my-service --type api --description "My first service"

# Check status
velora list
```

## 🔒 Security Considerations

### Binary Signing
```bash
# macOS code signing (requires Apple Developer cert)
codesign --sign "Developer ID Application: Your Name" dist/velora-cli-macos

# Windows code signing (requires code signing certificate)
signtool sign /f certificate.p12 /p password dist/velora-cli-win.exe
```

### Checksum Verification
```bash
# Generate checksums (already included in build script)
shasum -a 256 dist/velora-cli-* > dist/SHA256SUMS

# Users can verify downloads
shasum -a 256 -c SHA256SUMS
```

## 📈 Success Metrics

Track these metrics post-deployment:
- Download counts per platform
- Installation method popularity  
- CLI command usage statistics
- User retention and engagement
- Error rates and crash reports

## 🎯 Next Steps

1. **Immediate**: Publish to npm and create GitHub release
2. **Short-term**: Set up Homebrew tap and CDN distribution
3. **Long-term**: Create native package managers integration (apt, yum, choco)
4. **Advanced**: Auto-update mechanism and telemetry

---

**🎉 The Velora CLI is now ready for global distribution!**

This comprehensive guide ensures users can install Velora CLI through their preferred method, providing maximum accessibility and adoption potential.