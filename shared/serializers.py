from rest_framework import serializers

class DynamicModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional 'fields' argument to control
    which fields should be displayed.
    """
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            # If 'exclude' is provided, remove the specified fields
            for field_name in exclude:
                self.fields.pop(field_name, None)  # Use .pop(key, None) to avoid KeyError if field doesn't exist


class DynamicSerializer(serializers.Serializer):
    """
    A ModelSerializer that takes an additional 'fields' argument to control
    which fields should be displayed.
    """
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)