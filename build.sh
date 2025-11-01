#!/usr/bin/env bash
# build.sh

set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Automatically load initial JSON data
python manage.py load_initial_data