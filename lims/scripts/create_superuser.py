# scripts/create_superuser.py
# Used by the web frontend Travis CI to create a temporary superuser for running tests

from django.contrib.auth.models import User


def run():
    User.objects.create_superuser('test', 'test@example.com', 'test')
