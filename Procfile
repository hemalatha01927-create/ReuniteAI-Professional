web: flask --app run.py init-db && gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT run:app
