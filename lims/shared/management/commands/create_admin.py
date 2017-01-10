from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create an admin user (if not exists) with password from env'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='', dest='email')
        parser.add_argument('--password', type=str, default='', dest='pass')

    def handle(self, *args, **kwargs):

        admin_email = kwargs['email'] if kwargs['email'] else settings.SETUP_ADMIN_EMAIL
        admin_password = kwargs['pass'] if kwargs['pass'] else settings.SETUP_ADMIN_PASSWORD

        try:
            admin_user = User.objects.create_user('admin', admin_email, admin_password)
        except:
            pass

        try:
            admin_group = Group.objects.get(name='admin')
            staff_group = Group.objects.get(name='staff')
            user_group = Group.objects.get(name='user')
            admin_user.groups.add(admin_group, staff_group, user_group)
        except:
            pass
