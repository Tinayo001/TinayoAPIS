#!/bin/bash

# Set Django settings module automatically
export DJANGO_SETTINGS_MODULE="Mtambo.settings"

# Ensure Django is ready by running Django's "check" command to initialize the app registry
echo "Running Django check command..."
python manage.py check

# Apply migrations (in case there are any pending migrations)
echo "Applying migrations..."
python manage.py migrate

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A Mtambo.celery:app worker --loglevel=info &

# Start Celery beat scheduler in the background
echo "Starting Celery beat scheduler..."
celery -A Mtambo.celery:app beat --loglevel=info &

# Start Django development server
echo "Starting Django development server..."
python manage.py runserver

