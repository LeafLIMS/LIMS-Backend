# scripts/create_superuser.py
# Used by the web frontend Travis CI to create a temporary superuser for running tests

from django.contrib.auth.models import User


def run():
    try:
        User.objects.create_superuser('test', 'test@example.com', 'test')
    except:
        pass  # Ignore because if it already exists then the outcome is the same
