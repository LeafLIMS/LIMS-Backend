from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver


@receiver(post_save, sender=User)
def give_superuser_groups(sender, **kwargs):
    instance = kwargs['instance']
    if instance.is_superuser and kwargs['created']:
        # Add the staff and admin groups to the user
        staff_group = Group.objects.get(name='staff')
        admin_group = Group.objects.get(name='admin')
        instance.groups.add(staff_group)
        instance.groups.add(admin_group)
