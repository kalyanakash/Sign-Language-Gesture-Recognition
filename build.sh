#!/usr/bin/env bash
# This file tells Render how to build your app

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt
