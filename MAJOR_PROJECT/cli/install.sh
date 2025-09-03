#!/bin/bash

# Velora CLI Installation Script
# curl -fsSL https://get.velora.dev | sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/your-org/velora-cli"
BINARY_NAME="velora"
INSTALL_DIR="/usr/local/bin"

echo -e "${BLUE}🚀 Velora CLI Installer${NC}"
echo "======================"

# Detect OS and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case $OS in
  Linux*)
    PLATFORM="linux"
    ;;
  Darwin*)
    PLATFORM="darwin"
    ;;
  *)
    echo -e "${RED}❌ Unsupported operating system: $OS${NC}"
    exit 1
    ;;
esac

case $ARCH in
  x86_64)
    ARCH="amd64"
    ;;
  arm64|aarch64)
    ARCH="arm64"
    ;;
  *)
    echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
    exit 1
    ;;
esac

echo -e "${YELLOW}📋 Detected platform: ${PLATFORM}-${ARCH}${NC}"

# Check if running as root for system-wide installation
if [ "$EUID" -eq 0 ]; then
  INSTALL_DIR="/usr/local/bin"
  echo -e "${YELLOW}🔑 Installing system-wide to ${INSTALL_DIR}${NC}"
else
  # Try to use user's local bin directory
  if [ -d "$HOME/.local/bin" ]; then
    INSTALL_DIR="$HOME/.local/bin"
  elif [ -d "$HOME/bin" ]; then
    INSTALL_DIR="$HOME/bin"
  else
    mkdir -p "$HOME/.local/bin"
    INSTALL_DIR="$HOME/.local/bin"
  fi
  echo -e "${YELLOW}👤 Installing to user directory: ${INSTALL_DIR}${NC}"
fi

# Check if Node.js is available for npm installation
if command -v npm > /dev/null 2>&1; then
  echo -e "${GREEN}📦 Node.js detected, installing via npm...${NC}"
  
  npm install -g velora-cli
  
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Velora CLI installed successfully via npm!${NC}"
  else
    echo -e "${YELLOW}⚠️  NPM installation failed, falling back to binary installation...${NC}"
  fi
else
  echo -e "${YELLOW}📦 Node.js not found, installing binary...${NC}"
fi

# Verify installation
if command -v velora > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Installation successful!${NC}"
  echo ""
  velora --version
else
  # Add to PATH instructions
  echo -e "${YELLOW}⚠️  Velora CLI installed but not in PATH${NC}"
  echo -e "${BLUE}💡 Add to your PATH:${NC}"
  
  case $SHELL in
    */zsh)
      echo "echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
      echo "source ~/.zshrc"
      ;;
    */bash)
      echo "echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc"
      echo "source ~/.bashrc"
      ;;
    *)
      echo "export PATH=\"$INSTALL_DIR:\$PATH\""
      ;;
  esac
fi

echo ""
echo -e "${BLUE}🎉 Welcome to Velora CLI!${NC}"
echo -e "${YELLOW}🔧 Next steps:${NC}"
echo "1. Set up configuration: velora config setup"
echo "2. Create your first service: velora create my-service --type api"
echo "3. View help: velora --help"
echo ""
echo -e "${BLUE}📚 Documentation: https://docs.velora.dev${NC}"
echo -e "${BLUE}💬 Support: https://discord.gg/velora${NC}"