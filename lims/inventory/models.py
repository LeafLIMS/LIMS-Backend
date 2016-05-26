import re

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from mptt.models import MPTTModel, TreeForeignKey
from gm2m import GM2MField
from model_utils.managers import InheritanceManager
from jsonfield import JSONField

from lims.shared.models import Organism

class PartType(models.Model):
    """
    Provides a list of the different types of parts.
    """
    name = models.CharField(max_length=50)
    identifier = models.CharField(max_length=30, blank=True, null=True)
    of_type = models.ForeignKey('self', blank=True, null=True)

    def __str__(self):
        return self.name

class ItemType(MPTTModel):
    """
    Provides a tree based model of types, each which can have parents/children
    """
    name = models.CharField(max_length=150, unique=True, db_index=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def has_children(self):
        return True if self.get_descendant_count() > 0 else False

    def display_name(self):
        if self.level > 0:
            return '{} {}'.format('--' * self.level, self.name)
        return self.name

    def root(self):
        if self.parent:
            return self.parent.get_root().name
        return self.name

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class AmountMeasure(models.Model):
    """
    A named measurement and letter representation
    """
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return "{} ({})".format(self.name, self.symbol)

class Location(MPTTModel):
    """
    Provides a physical location for an item
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=6, unique=True, null=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def has_children(self):
        return True if self.get_descendant_count() > 0 else False

    def display_name(self):
        if self.level > 0:
            return '{} {}'.format('--' * self.level, self.name)
        return self.name

    def __str__(self):
        if self.parent:
            return '{} ({})'.format(self.name, self.parent.name)
        return self.name

class Set(models.Model):
    """
    A named set of items in the inventory
    """
    name = models.CharField(max_length=40)
    is_public = models.BooleanField(default=False)
    is_partset = models.BooleanField(default=False)

    def number_of_items(self):
        return self.items.count()

    def __str__(self):
        return self.name

class GenericItem(models.Model):
    """
    Represents the common base fields required for an item in a inventory.
    """
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=20, null=True, blank=True, db_index=True, unique=True)
    metadata = JSONField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    item_type = TreeForeignKey(ItemType)

    tags = models.ManyToManyField(Tag, blank=True)

    in_inventory = models.BooleanField(default=False)
    amount_available = models.IntegerField(default=0)
    amount_measure = models.ForeignKey(AmountMeasure)
    location = TreeForeignKey(Location, null=True, blank=True)

    added_by = models.ForeignKey(User)
    added_on = models.DateTimeField(auto_now_add=True)
    last_updated_on = models.DateTimeField(auto_now=True)

    objects = InheritanceManager()
    #related = RelatedObjectsDescriptor()
    #related = GM2MField()

    sets = GM2MField(Set, related_name='items', blank=True)

    def get_tags(self):
        return ", ".join([t.name for t in self.tags.all()])

    def of_type(self):
        obj = ContentType.objects.get_for_model(self)
        return obj.model.title()

    def location_path(self):
        return ' > '.join([x.name for x in self.location.get_ancestors(include_self=True)])

    def save(self, *args, **kwargs):
        if self.amount_available > 0:
            self.in_inventory = True
        super(GenericItem, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

class Part(GenericItem):
    """
    Represents a nucleotide part in the inventory 
    """
    sequence = models.TextField()
    originating_organism = models.ForeignKey(Organism, related_name='originating_organisms')
    optimised_for_organism = models.ForeignKey(Organism, blank=True, null=True, related_name='optimised_for_organisms')
    
    usage = models.IntegerField(default=0)

    def get_part_types(self):
        return self.part_type

    def __str__(self):
        return self.name

class Construct(GenericItem):
    """
    Represents a construct (e.g. a plasmid) in the inventory before it becomes a part
    """
    sequence = models.TextField()
    originating_organism = models.ForeignKey(Organism)

    def __str__(self):
        return self.name

class Enzyme(GenericItem):
    """
    Represents a enzyme in the inventory
    """
    cut_sequence = models.CharField(max_length=50, blank=True, null=True)
    recognition_sequence = models.CharField(max_length=50, blank=True, null=True)
    effective_length = models.FloatField(blank=True, null=True)
    overhang = models.CharField(max_length=20, blank=True, null=True)
    methylation_sensitivity = models.CharField(max_length=50, blank=True, null=True)

    def searchable_cut_sequence(self):
        return re.sub(r'[^A-Za-z]+', '', self.cut_sequence)

    def searchable_recognition_sequence(self):
        return re.sub(r'[^A-Za-z]+', '', self.recognition_sequence)

class Primer(GenericItem):
    """
    Represents a primer in the inventory
    """
    reference = models.CharField(max_length=50)
    product = models.CharField(max_length=100, blank=True, null=True)
    purification = models.CharField(max_length=100, blank=True, null=True)
    primer_sequence = models.CharField(max_length=100)
    gc_content = models.FloatField(verbose_name='GC content', blank=True, null=True)
    tm_c = models.FloatField(verbose_name='Tm (50mM NaCl) C', blank=True, null=True)
    # was required
    nmoles = models.FloatField(blank=True, null=True)
    modifications_and_services = models.CharField(max_length=100, blank=True, null=True)
    nmoles_od = models.FloatField(verbose_name='nmoles/OD', blank=True, null=True)
    # was required
    microg_od = models.FloatField(verbose_name='μg/OD', blank=True, null=True)
    bases = models.IntegerField(null=True, blank=True)

    def save(self, **kwargs):
        self.primer_sequence = re.sub(r'[^A-Za-z]', '', self.primer_sequence)
        super(Primer, self).save(**kwargs)

class Consumable(GenericItem):
    """
    Represents a consumable in the inventory
    """
