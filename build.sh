#!/usr/bin/env bash
# Exit on any error
set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python prolink/manage.py collectstatic --no-input

echo "=== Running database migrations ==="
python prolink/manage.py migrate --run-syncdb --no-input

echo "=== Deployment complete ==="
