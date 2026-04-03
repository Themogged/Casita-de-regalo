#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py ensure_superuser
gunicorn tienda_regalos.wsgi:application
