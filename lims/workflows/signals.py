from django.dispatch import receiver

from .models import TaskTemplate
from lims.permissions.signals import permissions_removed, permissions_changed
from lims.permissions.permissions import ViewPermissionsMixin


@receiver(permissions_changed, sender=TaskTemplate)
def change_field_permissions(sender, **kwargs):
    """
    Change all associated fields to match task permissions
    """
    try:
        task = TaskTemplate.objects.get(pk=kwargs['id'])
    except:
        return
    field_types = ('input', 'variable', 'step', 'output', 'calculation',)
    for ft in field_types:
        fields = getattr(task, ft + '_fields').all()
        for f in fields:
            ViewPermissionsMixin().assign_permissions(f, kwargs['permissions'])


@receiver(permissions_removed, sender=TaskTemplate)
def remove_field_permissions(sender, **kwargs):
    """
    Change all associated fields to match task permissions
    """
    try:
        task = TaskTemplate.objects.get(pk=kwargs['id'])
    except:
        return
    field_types = ('input', 'variable', 'step', 'output', 'calculation',)
    for ft in field_types:
        fields = getattr(task, ft + '_fields').all()
        for f in fields:
            ViewPermissionsMixin().unassign_permissions(f, kwargs['groups'])
