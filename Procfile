web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py setup_groups && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
