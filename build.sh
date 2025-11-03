#!/usr/bin/env bash
# Exit on any error
set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Collecting static files ==="
python prolink/manage.py collectstatic --no-input

echo "=== Checking current migration status ==="
python prolink/manage.py showmigrations

echo "=== Running database migrations ==="
# First try normal migrate
python prolink/manage.py migrate --no-input

# If tables don't exist, create them
echo "=== Ensuring all tables exist ==="
python prolink/manage.py migrate --run-syncdb --no-input

echo "=== Final migration status ==="
python prolink/manage.py showmigrations

echo "=== Verifying database structure ==="
python prolink/manage.py verify_db_structure

echo "=== Creating missing tables ==="
python prolink/manage.py create_missing_tables

echo "=== Checking for test user ==="
python prolink/manage.py check_user samp@gmail.com

echo "=== Deployment complete ==="
