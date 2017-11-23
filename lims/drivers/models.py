import os
import shutil
import re
import datetime

from django.db import models
import reversion

from lims.equipment.models import Equipment
from lims.datastore.models import DataFile


@reversion.register()
class Driver(models.Model):
    """
    Specifies a class that deals with a specific piece of equipment

    Uses a class_path attribute that points to the actual driver
    that deals with the equipment. This allows drivers to be
    switched on and off in a more simple fashion.
    """
    name = models.CharField(max_length=100)
    class_path = models.CharField(max_length=200,
                                  default='lims.drivers.packages.core.DummyDriver')
    equipment = models.ForeignKey(Equipment)

    is_enabled = models.BooleanField(default=True)

    def _get_class(name):
        """
        Get the class from a dotted path

        See class_path attribute for an example.
        """
        components = name.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    def get_driver(self):
        """
        Get an instance of the actual driver class from class_path
        """
        class_name = self._get_class(self.class_path)
        return class_name()

    def __str__(self):
        return self.name


@reversion.register()
class CopyFileDriver(models.Model):
    """
    A configurable copy-only driver for equipment.

    Is used to copy a set of files from a directory to another
    of just to create the relevant DataFile objects.
    """
    name = models.CharField(max_length=100)
    equipment = models.ForeignKey(Equipment, related_name='files_to_copy')

    copy_from_prefix = models.CharField(max_length=200, blank=True, null=True)
    copy_to_prefix = models.CharField(max_length=200, blank=True, null=True)

    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def fetch(self, interpolate_dict):
        result_paths = []
        for location in self.locations.all():
            rp = location.copy(interpolate_dict)
            if rp:
                result_paths.append(rp)
        return result_paths

    def __str__(self):
        return self.name


@reversion.register()
class CopyFilePath(models.Model):
    driver = models.ForeignKey(CopyFileDriver, related_name='locations')
    # All interpolation in {} for filename, e.g. {*.py} for python files
    # or /pth/to/{project_identifier}.txt
    # Available interpolates: project_identifier, product_indentifier,
    # date, run_identifier
    # If the prefix is present affix to path
    copy_from = models.CharField(max_length=200)
    copy_to = models.CharField(max_length=200, blank=True, null=True)

    INTERPOLATABLE_PATHS = (
        'project_identifier',
        'product_identifier',
        'run_identifier',
    )

    def __str__(self):
        return '{} -> {}'.format(self.copy_from, self.copy_to)

    def _interpolate_path(self, path, interpolate_dict, prefix=None):
        """
        Take a dict of interpolated values to generate path
        """
        # Find paths in dict
        # Match others and try to turn into date
        # If error return false?
        for pth in self.INTERPOLATABLE_PATHS:
            # Look for path in string path
            pattern = '{{{}}}'.format(pth)
            matches = re.findall(pattern, path)
            # If it has matches replace with interploate_dict value
            if len(matches) > 0:
                path = re.sub(pattern, interpolate_dict.get(pth, ''), path)
        # Lets try matching some dates now
        unmatched = re.findall('{.*}', path)
        for match in unmatched:
            # Try to convert to a date or at least strip
            # off the curly braces.
            potential_date = match.lstrip('{').rstrip('}')
            now = datetime.datetime.now()
            to_date = now.strftime(potential_date)
            path = re.sub(match, to_date, path)
        if prefix:
            path = os.path.join(prefix, path)
        return path

    def copy_from_path(self, interpolate_dict):
        prefix = None
        if self.driver.copy_from_prefix:
            prefix = self.driver.copy_from_prefix
        return self._interpolate_path(self.copy_from, interpolate_dict, prefix)

    def copy_to_path(self, interpolate_dict):
        prefix = None
        if self.driver.copy_to_prefix:
            prefix = self.driver.copy_to_prefix
        return self._interpolate_path(self.copy_to, interpolate_dict, prefix)

    def copy(self, interpolate_dict):
        # Don't forget you need to create a datastore item
        # to ensure the file isn't lost
        from_location = self.copy_from_path(interpolate_dict)
        to_location = self.copy_to_path(interpolate_dict)
        try:
            file_loc = shutil.copy2(from_location, to_location)
        except IOError as e:
            return False
        else:
            file_name = to_location.rsplit('/', 1)[1]
            ds = DataFile(
                file_name=file_name,
                location=file_loc,
                equipment=self.driver.equipment)
            ds.save()
            return ds
