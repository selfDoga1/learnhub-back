from core.models import Group
from tags.models import TagCorrelation, UUIDTag


def _get_pairs(tags):
    tags = sorted(tags, key=lambda t: str(t.id))
    pairs = set()
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            pairs.add((tags[i], tags[j]))
    return pairs

def _process_correlations(removed_pairs):
    for tag1, tag2 in removed_pairs:
        try:
            correlation = TagCorrelation.objects.get(source=tag1, target=tag2)
            correlation.weight = max(0, correlation.weight - 1.0)
            correlation.save()
        except TagCorrelation.DoesNotExist:
            pass


def update_tag_correlations_from_tag_lists(old_tag_names, new_tag_names):
    # Fetch tag objects by names
    old_tags = set(UUIDTag.objects.filter(name__in=old_tag_names))
    new_tags = set(UUIDTag.objects.filter(name__in=new_tag_names))

    old_pairs = _get_pairs(old_tags)
    new_pairs = _get_pairs(new_tags)

    added_pairs = new_pairs - old_pairs
    removed_pairs = old_pairs - new_pairs

    # Increment weight for newly added pairs only
    for tag1, tag2 in added_pairs:
        correlation, created = TagCorrelation.objects.get_or_create(
            source=tag1,
            target=tag2,
            defaults={'weight': 1.0}
        )
        if not created:
            correlation.weight += 1.0
            correlation.save()

    # Decrement weight for removed pairs only
    _process_correlations(removed_pairs)

    TagCorrelation.objects.filter(weight=0).delete()


def update_tag_correlations_on_group_delete(group_id):
    # Fetch the group and its tags before deletion
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return  # Group already deleted or invalid ID

    group_tags = set(group.areas.all())

    # All pairs from the group's tags need to be decremented (removed)
    removed_pairs = _get_pairs(group_tags)

    # Decrement weight for removed pairs only
    _process_correlations(removed_pairs)

    # Cleanup zero-weight correlations
    TagCorrelation.objects.filter(weight=0).delete()
