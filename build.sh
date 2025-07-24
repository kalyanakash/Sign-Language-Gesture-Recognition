#!/usr/bin/env bash
# This file tells Render how to build your app

set -o errexit  # exit on error

# Upgrade pip and setuptools first
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

# Install dependencies
pip install --no-cache-dir -r requirements.txt
