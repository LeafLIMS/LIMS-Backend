class SerializerMixin:

    def get_serializer_class_from_name(self, name):
        serializer_name = name + 'Serializer'
        print(globals())
        serializer_class = globals()[serializer_name]
        return serializer_class
