from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group, Permission


class UserAppConfig(AppConfig):
    name = 'lims.users'
    verbose_name = 'Users'

    def ready(self):
        # Create the default set of user groups and
        # assign the correct permissions.
        for group in settings.DEFAULT_GROUPS:
            try:
                Group.objects.get(name=group)
            except ObjectDoesNotExist:
                g = Group(name=group)
                g.save()
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
