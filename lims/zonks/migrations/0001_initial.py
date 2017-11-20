# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-20 15:23
from __future__ import unicode_literals

from django.db import migrations

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.management import create_permissions

def make_groups(apps, schema_editor):
    # Create the default set of user groups and
    # assign the correct permissions.

    # Permissions aren't created until after all migrations
    # are run so lets create them now!
    app_configs = apps.get_app_configs()
    for app in app_configs:
        app.models_module = True
        create_permissions(app, verbosity=0)
        app.models_module = None

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
    ]

    operations = [
        migrations.RunPython(make_groups)
    ]
