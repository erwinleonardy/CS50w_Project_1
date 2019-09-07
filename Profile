web: gunicorn src:app
heroku ps:scale web=1
