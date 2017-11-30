import os
import importlib


PLUGIN_DIRECTORIES = ('dist', 'external')


class PluginMountPoint(type):
    """
    The base class for establishing a mount point

    All mount points inherit this as a metaclass so allowing the easy listing of plugins.
    """
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = []
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins.append(cls)

    def get_plugins(cls, *args, **kwargs):
        return [p(*args, **kwargs) for p in cls.plugins]


def list_plugins():
    modules = []
    for pd in PLUGIN_DIRECTORIES:
        for d in os.scandir('./lims/plugins/'+pd):
            if not d.name.startswith('__') and (d.name.endswith('.py') or d.is_dir()):
                without_ext = d.name.rsplit('.', 1)
                modules.append((pd, without_ext[0]))
    return modules


def load_plugins(**kwargs):
    plugin_path = 'lims.plugins.{dir}.{module}'
    plugins_to_load = list_plugins()
    for plugin in plugins_to_load:
        path = plugin_path.format(dir=plugin[0], module=plugin[1])
        importlib.import_module(path)


class ExamplePluginProvider:
    __metaclass__ = PluginMountPoint
