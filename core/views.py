import copy
from collections import defaultdict
from datetime import datetime
from itertools import chain

import pytz
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from tags.models import RelatedTag, TagCorrelation
from upload.models import ImageUpload
from .models import User, Group, GroupMember, Activity
from .permissions import IsGroupAdminOrMemberReadOnly, IsGroupAdminOrSelfManage, IsSelfReadUpdateOnly
from .serializers import UserSerializer, GroupSerializer, GroupMemberSerializer, ActivitySerializer


def _get_activities_by_user(user):
    memberships = GroupMember.objects.filter(user=user, is_pending_approval=False).prefetch_related('group')
    groups = [member.group for member in memberships]
    activities = Activity.objects.filter(group__in=groups)

    return activities


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSelfReadUpdateOnly]

    def partial_update(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data.copy()
        avatar = data.pop('avatar', None)
        interests = data.pop('interests', None)

        if avatar and user.avatar:
            image_upload = user.avatar
            image_upload.file.delete(save=False)
            image_upload.file = avatar[0]
            image_upload.save()

        if interests is not None:
            user.interests.set(interests)

        request._full_data = data
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def groups(self, request):
        user = self.request.user
        memberships = (
            GroupMember.objects.filter(
                user=user, is_pending_approval=False
            )
            .prefetch_related('group')
            .order_by('-is_owner', '-is_admin')
        )
        groups = [member.group for member in memberships]
        serializer = GroupSerializer(groups, many=True, context={'user': user})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def activities(self, request):
        user = self.request.user
        activities = _get_activities_by_user(user)
        serializer = ActivitySerializer(activities, many=True, context={'user': user})

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def activities_by_date(self, request):
        date = self.request.query_params.get('date', None)

        if not date:
            return Response({'detail': _('Invalid or missing date parameter.')}, status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user
        activities = _get_activities_by_user(user)
        activities = activities.filter(datetime__date=date)
        serializer = ActivitySerializer(activities, many=True, context={'user': user})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        user = self.request.user
        serializer = UserSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsGroupAdminOrMemberReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        owner = self.request.user
        data = request.data.copy()
        areas = data.pop('areas', None)
        file = request.FILES.get('cover')

        if not file:
            return Response({'detail': _('Invalid or missing group cover.')}, status=status.HTTP_400_BAD_REQUEST)

        cover = (
            ImageUpload.objects.create(
                owner=owner,
                file=file,
            )
        )

        group = (
            Group.objects.create(
                name=data['name'],
                description=data['description'],
                visibility=data['visibility'],
                cover=cover,
            )
        )

        if areas is not None:
            group.areas.set(areas)

        GroupMember.objects.create(
            group=group,
            user=owner,
            is_owner=True,
            is_admin=False,
            is_pending_approval=False,
        )

        return Response(status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy()
        group = self.get_object()
        cover = data.pop('cover', None)
        areas = data.pop('areas', None)

        if cover:
            image_upload = group.cover
            image_upload.file.delete(save=False)
            image_upload.file = cover[0]
            image_upload.save()

        if areas is not None:
            group.areas.set(areas)

        request._full_data = data

        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def home(self, request):
        user = request.user
        user_tags = list(user.interests.all())
        user_tag_ids = set(tag.id for tag in user_tags)
        weighted_tag_ids = defaultdict(float)

        for related in RelatedTag.objects.filter(tag__in=user_tags):
            weighted_tag_ids[related.related_id] += 1.0

        for corr in TagCorrelation.objects.filter(source__in=user_tags):
            weighted_tag_ids[corr.target_id] += corr.weight

        for tag_id in user_tag_ids:
            weighted_tag_ids[tag_id] += 2.0

        related_group_qs = self.get_queryset().filter(areas__in=weighted_tag_ids.keys()).distinct()

        group_scores = []
        for group in related_group_qs:
            group_tag_ids = set(group.areas.values_list("id", flat=True))
            score = sum(weighted_tag_ids[tag_id] for tag_id in group_tag_ids if tag_id in weighted_tag_ids)
            group_scores.append((group, score))

        sorted_groups = [g for g, _ in sorted(group_scores, key=lambda x: x[1], reverse=True)]
        unrelated_groups = self.get_queryset().exclude(id__in=[g.id for g in sorted_groups])
        final_groups = list(chain(sorted_groups, unrelated_groups))

        paginator = PageNumberPagination()
        paginated_groups = paginator.paginate_queryset(final_groups, request)
        serializer = self.get_serializer(paginated_groups, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        group = self.get_object()
        activities = group.activities.all()
        serializer = ActivitySerializer(activities, many=True, exclude=['group'])

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        user = self.request.user
        group = self.get_object()

        group_members = (
            group.members.select_related('user').all()
            .order_by('-is_owner', '-is_admin', '-is_pending_approval', '-user__name')
        )

        if not (group.is_owner(user) or group.is_admin(user)):
            group_members = group_members.filter(is_pending_approval=False)

        serializer = GroupMemberSerializer(
            group_members,
            many=True,
            fields=['id', 'user', 'is_admin', 'is_owner', 'is_pending_approval']
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def exit(self, request, pk=None):
        group = self.get_object()
        user = self.request.user
        group_member = GroupMember.objects.get(group=group, user=user)
        group_member.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def enter(self, request, pk=None):
        group = self.get_object()
        user = self.request.user
        GroupMember.objects.get_or_create(group=group, user=user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def create_request(self, request, pk=None):
        group = self.get_object()

        GroupMember.objects.get_or_create(
            group=group,
            user=request.user,
            is_pending_approval=True
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def handle_request(self, request, pk=None):
        group = self.get_object()
        data = request.data.copy()

        user = data.get('user', None)
        if not user:
            return Response({'detail': _('Missing user Id')}, status=status.HTTP_400_BAD_REQUEST)

        action = data.get('action', None)

        group_member = GroupMember.objects.get(group=group, user=user)

        if action:
            group_member.is_pending_approval = False
            group_member.save()
        else:
            group_member.delete()

        return Response(status.HTTP_204_NO_CONTENT)


class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [IsAuthenticated, IsGroupAdminOrSelfManage]

    @action(detail=True, methods=['post'])
    def handle_privilege(self, request, pk=None):
        group_member = self.get_object()
        data = request.data.copy()
        privilege = data.get('privilege', None)

        if privilege == 'admin':
            group_member.is_admin = True

        if privilege == 'user':
            group_member.is_admin = False

        group_member.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, IsGroupAdminOrMemberReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context

    def create(self, request, *args, **kwargs):

        data = request.data.copy()

        group_member = (
            GroupMember.objects.filter(
                group__pk=data['group'],
                user=self.request.user,
            ).first()
        )

        if not group_member or (not group_member.is_admin and not group_member.is_owner):
            return Response(status=status.HTTP_403_FORBIDDEN)

        _datetime = data.get("datetime")
        _datetime = datetime.strptime(_datetime, "%a, %d %b %Y %H:%M:%S GMT")
        _datetime = pytz.utc.localize(_datetime)

        Activity.objects.create(
            name=data['name'],
            description=data['description'],
            modality=data['modality'],
            address=data.get('address', None),
            link=data.get('link', None),
            group=group_member.group,
            creator=self.request.user,
            datetime=_datetime,
        )

        return Response(status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def occupied_days(self, request, pk=None):
        date = self.request.query_params.get('date', None)

        if not date:
            return Response({'detail': _('Invalid or missing date parameter.')}, status=status.HTTP_400_BAD_REQUEST)

        date = datetime.strptime(date[:10], '%Y-%m-%d').date()
        user = self.request.user
        activities = _get_activities_by_user(user).filter(datetime__month=date.month, datetime__year=date.year)
        occupied_days = activities.values_list('datetime__day', flat=True).distinct().order_by('datetime')

        return Response({
            'year': date.year,
            'month': date.month,
            'days': list(occupied_days),
        }, status=status.HTTP_200_OK)


class PublicViewSet(ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='sign-up')
    def sign_up(self, request, *args, **kwargs):
        data = request.data.copy()
        avatar = data.pop('avatar', None)
        data = {key: value for key, value in data.items()}

        with transaction.atomic():
            raw_password = data.pop('password')
            user = User.objects.create(**data)
            user.set_password(raw_password)

            if avatar:
                image_upload = ImageUpload.objects.create(
                    file=avatar[0],
                    owner=user,
                    name=f'{user.name} - avatar'
                )
                user.avatar = image_upload

            user.save()

        return Response(status=status.HTTP_201_CREATED)
