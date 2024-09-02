#!/usr/bin/env bash

function manage_app() {
    python manage.py makemigrations
    python manage.py migrate
    python manage.py collectstatic --no-input
}

if [ "${SERVER_ENVIRONMENT}" == "local" ]
then
    # use local server
    manage_app
    # use django runserver as development server here.
    python manage.py runserver 0.0.0.0:8000
else
    # use production/staging server
    manage_app
    # use gunicorn for production server here
    gunicorn hr_base.wsgi:application --workers 4 --timeout 60 --bind 0.0.0.0:8000 --chdir=/app
fi
