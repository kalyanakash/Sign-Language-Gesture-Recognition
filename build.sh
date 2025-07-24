#!/usr/bin/env bash
# Simple build script for Render - Python 3.11 compatible
# Updated: 2025-07-25

set -o errexit  # exit on error

echo "Starting clean build..."
# Install basic Flask dependencies only
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
echo "Build completed successfully!"
