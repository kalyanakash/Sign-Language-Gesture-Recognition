#!/usr/bin/env bash
# Complete build script for Render - ALL PACKAGES
# Updated: 2025-07-25

set -o errexit  # exit on error

echo "Starting COMPLETE build with ALL packages..."

# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# Install packages step by step for better error tracking
echo "Installing Flask ecosystem..."
pip install --no-cache-dir Flask==2.2.5 Werkzeug==2.2.3 gunicorn==21.2.0

echo "Installing Flask extensions..."
pip install --no-cache-dir flask-cors==4.0.0 flask-sqlalchemy==3.0.5 flask-login==0.6.3
pip install --no-cache-dir flask-bcrypt==1.0.1 flask-mail==0.9.1 flask-wtf==1.0.1

echo "Installing core dependencies..."
pip install --no-cache-dir itsdangerous==2.1.2 WTForms==3.0.1 MarkupSafe==2.1.3 Jinja2==3.1.2

echo "Installing scientific packages..."
pip install --no-cache-dir numpy==1.24.3
pip install --no-cache-dir scikit-learn==1.3.0

echo "Installing computer vision packages..."
pip install --no-cache-dir opencv-python-headless==4.8.0.74
pip install --no-cache-dir mediapipe==0.10.2

echo "Installing additional packages..."
pip install --no-cache-dir matplotlib==3.7.2 pillow==10.0.0
pip install --no-cache-dir python-socketio==5.8.0 eventlet==0.33.3

echo "Build completed successfully - ALL PACKAGES INSTALLED!"
