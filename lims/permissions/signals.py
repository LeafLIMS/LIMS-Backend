from django import dispatch


permissions_changed = dispatch.Signal(providing_args=['id', 'permissions'])
permissions_removed = dispatch.Signal(providing_args=['id', 'groups'])
