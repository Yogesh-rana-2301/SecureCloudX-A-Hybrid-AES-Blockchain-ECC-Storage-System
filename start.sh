#!/bin/bash

# SecureCloudX Quick Start Script
# This script sets up and runs SecureCloudX

set -e  # Exit on error

echo " SecureCloudX - Quick Start Script"
echo "===================================="

# Check Python version
echo " Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo " Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo " Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo " Creating directories..."
mkdir -p storage/files
mkdir -p blockchain

# Run the application
echo ""
echo " Setup complete! Starting SecureCloudX..."
echo ""
echo " Server will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
