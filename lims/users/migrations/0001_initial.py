# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.management import create_permissions

def make_groups(apps, schema_editor):
    # Create the default set of user groups and
    # assign the correct permissions.

    # Permissions aren't created until after all migrations
    # are run so lets create them now!
    apps.models_module = True
    create_permissions(apps, verbosity=0)
    apps.models_module = None

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for group in settings.DEFAULT_GROUPS:
        g,created = Group.objects.get_or_create(name=group)
        if group == 'admin':
            # Assign all available permissions to the admin group
            p = list(Permission.objects.all())
            g.permissions.add(*p)
        elif group == 'staff':
            for perm in settings.DEFAULT_STAFF_PERMISSIONS:
                p = Permission.objects.get(name=perm)
                g.permissions.add(p)
        elif group == 'user':
            # Default permissions for users are store in
            # the settings.py file
            for perm in settings.DEFAULT_USER_PERMISSIONS:
                p = Permission.objects.get(name=perm)
                g.permissions.add(p)

class Migration(migrations.Migration):

    dependencies = [
        # These two are required to ensure the necessary
        # prerequisites are present and we can use their
        # models.
        # ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
        # Kinda a cheat but workflows is the last app
        # so it'll only run after all the others!
        # ('workflows', '__latest__'),
    ]

    operations = [
        migrations.RunPython(make_groups)
    ]
