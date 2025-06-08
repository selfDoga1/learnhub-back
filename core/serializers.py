from rest_framework import serializers
from taggit.serializers import TagListSerializerField

from shared.serializers import DynamicModelSerializer
from .models import User, Group, GroupMember, Activity


class UserSerializer(DynamicModelSerializer):
    interests = TagListSerializerField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar', 'interests']




class GroupSerializer(DynamicModelSerializer):
    members = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_pending_approval = serializers.SerializerMethodField()
    areas = TagListSerializerField()

    def get_members(self, obj):
        user = self.context['user']
        is_member = obj.is_member(user)
        group_members = obj.members_list()
        count = group_members.count()

        if (is_member or obj.visibility == Group.Visibility.PUBLIC) and count > 0:
            return (
                GroupMemberSerializer(
                    group_members,
                    many=True,
                    context=self.context,
                    fields=['user', 'is_admin', 'is_owner', 'is_pending_approval']
                ).data
            )

        return count

    def get_owner(self, obj):
        owner = obj.owner()
        return (
            UserSerializer(
                owner.user,
                many=False,
                context=self.context,
                fields=['id', 'name', 'avatar']
            ).data
        )

    def get_is_owner(self, obj):
        user = self.context['user']
        return obj.is_owner(user)

    def get_is_admin(self, obj):
        user = self.context['user']
        return obj.is_admin(user)

    def get_is_member(self, obj):
        user = self.context['user']
        return obj.is_member(user)

    def get_is_pending_approval(self, obj):
        user = self.context['user']
        return obj.members.select_related('user').filter(user=user, is_pending_approval=True).exists()

    class Meta:
        model = Group
        fields = (
            [
                'id', 'name', 'description', 'cover', 'visibility', 'members',
                'owner', 'is_owner', 'is_admin', 'is_member', 'is_pending_approval',
                'areas'
            ]
        )


class GroupMemberSerializer(DynamicModelSerializer):
    user = UserSerializer(read_only=True, fields=['id', 'name', 'avatar', 'email'])

    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user', 'is_owner', 'is_admin', 'is_pending_approval']


class ActivitySerializer(DynamicModelSerializer):
    group = GroupSerializer(read_only=True, fields=['id', 'name', 'cover', 'owner', 'visibility', 'members', 'is_owner', 'is_admin', 'is_member'])

    class Meta:
        model = Activity
        fields = ['id', 'name', 'description', 'datetime', 'group', 'address', 'link', 'modality']
