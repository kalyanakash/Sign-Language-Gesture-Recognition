#!/usr/bin/env bash
# Simple build script for Render

set -o errexit

# Use the simple requirements first
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir Flask==3.0.2
pip install --no-cache-dir gunicorn==21.2.0
pip install --no-cache-dir flask-cors==4.0.0
pip install --no-cache-dir flask-sqlalchemy==3.0.5
pip install --no-cache-dir flask-login==0.6.3
pip install --no-cache-dir flask-wtf==1.1.1
pip install --no-cache-dir flask-bcrypt==1.0.1
pip install --no-cache-dir flask-mail==0.9.1
pip install --no-cache-dir itsdangerous==2.1.2
pip install --no-cache-dir WTForms==3.0.1
