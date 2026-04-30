# Procfile (used by Railway and Heroku-style deploys)
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --worker-class gthread --threads 2 --timeout 120 --access-logfile - --error-logfile -
worker: celery -A config worker -l WARNING --concurrency=4
beat: celery -A config beat -l WARNING --scheduler django_celery_beat.schedulers:DatabaseScheduler
