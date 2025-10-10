#!/usr/bin/env bash
# Exit on any error
set -e

# Install dependencies
pip install -r requirements.txt

# Collect static files
python prolink/manage.py collectstatic --no-input

# Run database migrations
python prolink/manage.py migrate
