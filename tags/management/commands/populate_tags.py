import json
import os
from django.core.management.base import BaseCommand
from tags.models import UUIDTag, RelatedTag


class Command(BaseCommand):
    help = 'Popula o banco de dados com tags e relações manuais a partir de um JSON'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(__file__)
        json_path = os.path.join(base_dir, 'tag_data.json')

        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR(f"JSON file no found: {json_path}"))
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        name_to_tag = {}

        for tag_data in data.get("tags", []):
            tag, _ = UUIDTag.objects.get_or_create(name=tag_data["name"])
            name_to_tag[tag.name] = tag
            self.stdout.write(self.style.SUCCESS(f"Tag created: {tag.name}"))

        for rel in data.get("related_tags", []):
            tag = name_to_tag.get(rel["tag"])
            related = name_to_tag.get(rel["related"])
            if tag and related:
                RelatedTag.objects.get_or_create(tag=tag, related=related)
                self.stdout.write(self.style.SUCCESS(f"RelatedTag: {tag.name} → {related.name}"))

        self.stdout.write(self.style.SUCCESS("Tags populated"))
