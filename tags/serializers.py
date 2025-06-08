from rest_framework import serializers
from taggit.models import Tag
from .models import RelatedTag, TagCorrelation, UUIDTag


class UUIDTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = UUIDTag
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class RelatedTagSerializer(serializers.ModelSerializer):
    tag = TagSerializer(read_only=True)
    related = TagSerializer(read_only=True)

    class Meta:
        model = RelatedTag
        fields = ['id', 'tag', 'related']


class TagCorrelationSerializer(serializers.ModelSerializer):
    source = TagSerializer(read_only=True)
    target = TagSerializer(read_only=True)

    class Meta:
        model = TagCorrelation
        fields = ['id', 'source', 'target', 'weight']
