import inspect

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import six

from rest_framework.utils import model_meta
from gm2m.helpers import GM2MTo

"""
Monkey patch the _resolve_model function to deal with
gm2m returning an instance of a GM2MTo object rather
than a class or string. Return the concrete class
instead as a stopgap measure.
"""


def _resolve_model(obj):
    """
    Resolve supplied `obj` to a Django model class.

    `obj` must be a Django model class itself, or a string
    representation of one.  Useful in situations like GH #1225 where
    Django may not have resolved a string-based reference to a model in
    another model's foreign key definition.

    String representations should have the format:
        'appname.ModelName'
    """
    if isinstance(obj, six.string_types) and len(obj.split('.')) == 2:
        app_name, model_name = obj.split('.')
        resolved_model = apps.get_model(app_name, model_name)
        if resolved_model is None:
            msg = "Django did not return a model for {0}.{1}"
            raise ImproperlyConfigured(msg.format(app_name, model_name))
        return resolved_model
    elif inspect.isclass(obj) and issubclass(obj, models.Model):
        return obj
    elif isinstance(obj, GM2MTo):
        return obj._meta.concrete_model
    raise ValueError("{0} is not a Django model".format(obj))

model_meta._resolve_model = _resolve_model


def _get_to_field(field):
    return getattr(field, 'to_fields', None) and field.to_fields[0]

model_meta._get_to_field = _get_to_field
