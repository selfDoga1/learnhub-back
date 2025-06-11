# from django.db.models.signals import m2m_changed
# from django.dispatch import receiver
# from taggit.models import Tag
#
# from core.models import User, Group
# from tags.models import UUIDTag, TagCorrelation
#
#
# def update_tag_correlations_from_tag_list(tag_list):
#     tags = list(UUIDTag.objects.filter(id__in=[t.id if isinstance(t, UUIDTag) else t for t in tag_list]))
#
#     for i in range(len(tags)):
#         for j in range(i + 1, len(tags)):
#             tag1, tag2 = sorted([tags[i], tags[j]], key=lambda t: str(t.id))
#
#             correlation, created = TagCorrelation.objects.get_or_create(
#                 source=tag1,
#                 target=tag2,
#                 defaults={'weight': 1.0}
#             )
#             if not created:
#                 correlation.weight += 1.0
#                 correlation.save()
#
#
#
# @receiver(m2m_changed, sender=User.interests.through)
# def update_tags_correlations(sender, instance, action, **kwargs):
#
#     if action in ["post_add", "post_remove", "post_clear"]:
#         tags = None
#
#         if isinstance(instance, User):
#             tags = instance.interests.all()
#         if isinstance(instance, Group):
#             tags = instance.areas.all()
#
#         if tags:
#             update_tag_correlations_from_tag_list(tags)
#
#
