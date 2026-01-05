#!/bin/bash
# Setup script for Simple RAG Pipeline
# Run this on a fresh Ubuntu 24.04 LTS server

set -e  # Exit on any error

echo "=========================================="
echo "Simple RAG Pipeline - System Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "Please do not run this script as root/sudo"
   echo "It will prompt for sudo when needed"
   exit 1
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install core system dependencies
echo ""
echo "Installing core system dependencies..."
sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  sqlite3 \
  make \
  git \
  curl \
  wget

# Install Playwright system dependencies for Ubuntu 24.04
echo ""
echo "Installing browser dependencies for Playwright..."
sudo apt install -y \
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libpango-1.0-0 \
  libcairo2 \
  libxshmfence1 \
  libglib2.0-0

# Handle the virtual package for Ubuntu 24.04
echo ""
echo "Installing audio libraries..."
if apt-cache show libasound2t64 >/dev/null 2>&1; then
  sudo apt install -y libasound2t64
else
  sudo apt install -y libasound2
fi

echo ""
echo "✓ System dependencies installed!"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Create and activate virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "2. Install Python packages and Playwright:"
echo "   make setup"
echo ""
echo "3. Configure your site:"
echo "   nano settings.yaml"
echo "   (Update the sitemap_url)"
echo ""
echo "4. Run the pipeline:"
echo "   make stage1"
echo "   make stage2"
echo "   make stage3"
echo "   make stage4"
echo ""
echo "=========================================="
