from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create an admin user (if not exists) with password from env'

    def handle(self, *args, **kwargs):

        admin_email = settings.SETUP_ADMIN_EMAIL
        admin_password = settings.SETUP_ADMIN_PASSWORD

        try:
            admin_user = User.objects.create_user('admin', admin_email, admin_password)
        except:
            pass

        try:
            admin_group = Group.objects.get(name='admin')
            staff_group = Group.objects.get(name='staff')
            admin_user.groups.add(admin_group, staff_group)
        except:
            pass
