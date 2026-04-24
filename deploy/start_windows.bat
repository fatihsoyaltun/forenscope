@echo off
call venv\Scripts\activate
set DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py migrate --noinput
python manage.py collectstatic --noinput
waitress-serve --port=8000 --threads=4 config.wsgi:application
