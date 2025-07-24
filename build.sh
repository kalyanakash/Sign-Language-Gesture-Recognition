#!/usr/bin/env bash
# Simple build script for Render - Python 3.11 compatible

set -o errexit  # exit on error

# Install basic Flask dependencies only
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
