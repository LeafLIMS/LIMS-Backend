import csv
from itertools import groupby

from lims.shared.models import Organism
from lims.inventory.models import ItemType, Item, Location, AmountMeasure


def get_serializer_class_from_name(name):
    serializer_name = name + 'Serializer'
    serializer_class = globals()[serializer_name]
    return serializer_class


def serialized_item_lookup(item_type: ItemType, item_identifier: str):
    """
    Given an item type and identifier return a serialized version.
    """
    item_type_name = item_type.get_root()
    try:
        item = Item.objects.get_subclass(
            item_type__name=item_type_name,
            identifier=item_identifier)
    except:
        return False
    serializer_class = get_serializer_class_from_name(item.__class__.__name__)
    serializer = serializer_class(item)
    return serializer.data


def item_from_type(item_type: ItemType, item_identifier: str, name: str, request, sequence=''):
    """
    Given an item type and identifier either return an already
    existing item from the inventory or create an empty item.
    """
    org, created = Organism.objects.get_or_create(name='Unknown')
    loc, created = Location.objects.get_or_create(name='Lab', code='L')
    measure = AmountMeasure.objects.get(name='Microlitres')
    defaults = {
        'name': name,
        'item_type': item_type,
        'location': loc.code,
        'amount_measure': measure,
        'added_by': request.user,
        'originating_organism': org,
        'sequence': sequence,
        'primer_sequence': sequence,
        'reference': item_identifier,
    }
    class_name = item_type.get_root().name
    serializer_class = get_serializer_class_from_name(class_name)
    try:
        item_class = globals()[class_name]
        item = item_class.objects.get(identifier=item_identifier)
    except:
        s_item = serializer_class(data=defaults)
        if s_item.is_valid(raise_exception=True):
            s_item.save()
            item = s_item.instance
    return item


def csv_to_items(items_file, request):
    """
    Convert a CSV file of items into database entries
    """
    csv_file = csv.DictReader(items_file)
    sorted_items = sorted(csv_file, key=lambda x: x['item_type'])
    grouped = groupby(sorted_items, key=lambda x: x['item_type'])

    rejects = []
    saved = []
    for grp, itms in grouped:
        items = []
        for i in itms:
            i['added_by'] = request.user.username
            items.append(i)
        try:
            item_type = ItemType.objects.get(name=grp)
        except:
            rejects = rejects + items

        if item_type:
            item_to_make_type = item_type.get_root()
            serializer_class = get_serializer_class_from_name(item_to_make_type.name)
            to_create = serializer_class(data=items, many=True)
            if to_create.is_valid():
                to_create.save()
                saved = saved + to_create.data
            else:
                with_errors = []
                for i, item in enumerate(items):
                    item['errors'] = to_create.errors[i]
                    with_errors.append(item)
                rejects = rejects + with_errors
    return (saved, rejects)
