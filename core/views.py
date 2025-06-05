from datetime import datetime

import pytz
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from upload.models import ImageUpload
from .models import User, Group, GroupMember, Activity
from .permissions import IsGroupAdminOrMemberReadOnly, IsGroupAdminOrSelfManage, IsSelfReadUpdateOnly
from .serializers import UserSerializer, GroupSerializer, GroupMemberSerializer, ActivitySerializer


def _get_activities_by_user(user):
    memberships = GroupMember.objects.filter(user=user, is_pending_approval=False).prefetch_related('group')
    groups = [member.group for member in memberships]
    activities = Activity.objects.filter(group__in=groups)

    return activities


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


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSelfReadUpdateOnly]

    def partial_update(self, request, *args, **kwargs):
        user = self.request.user
        data = request.data.copy()
        avatar = data.pop('avatar', None)

        if avatar and user.avatar:
            image_upload = user.avatar
            image_upload.file.delete(save=False)
            image_upload.file = avatar[0]
            image_upload.save()

        request._full_data = data
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def groups(self, request):
        user = self.request.user
        memberships = GroupMember.objects.filter(user=user, is_pending_approval=False).prefetch_related('group')
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
        _date = self.request.query_params.get('date', None)

        if not _date:
            return Response({'detail': _('Invalid or missing date parameter.')}, status=status.HTTP_400_BAD_REQUEST)

        user = self.request.user
        activities = _get_activities_by_user(user)
        activities = activities.filter(datetime__date=_date)
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
        _file = request.FILES.get('cover')

        if not _file:
            return Response({'detail': _('Invalid or missing group cover.')}, status=status.HTTP_400_BAD_REQUEST)

        cover = (
            ImageUpload.objects.create(
                owner=owner,
                file=_file,
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

        if cover:
            image_upload = group.cover
            image_upload.file.delete(save=False)
            image_upload.file = cover[0]
            image_upload.save()

        request._full_data = data

        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def home(self, request):
        groups = self.get_queryset()
        serializer = self.get_serializer(groups, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

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

        _user = data.get('user', None)
        if not _user:
            return Response({'detail': _('Missing user Id')}, status=status.HTTP_400_BAD_REQUEST)

        _action = data.get('action', None)

        group_member = GroupMember.objects.get(group=group, user=_user)

        if _action:
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

        _group_member = (
            GroupMember.objects.filter(
                group__pk=data['group'],
                user=self.request.user,
            ).first()
        )

        if not _group_member or (not _group_member.is_admin and not _group_member.is_owner):
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
            group=_group_member.group,
            creator=self.request.user,
            datetime=_datetime,
        )

        return Response(status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def occupied_days(self, request, pk=None):
        _date = self.request.query_params.get('date', None)

        if not _date:
            return Response({'detail': _('Invalid or missing date parameter.')}, status=status.HTTP_400_BAD_REQUEST)

        _date = datetime.strptime(_date[:10], '%Y-%m-%d').date()
        user = self.request.user
        activities = _get_activities_by_user(user).filter(datetime__month=_date.month, datetime__year=_date.year)
        occupied_days = activities.values_list('datetime__day', flat=True).distinct().order_by('datetime')

        return Response({
            'year': _date.year,
            'month': _date.month,
            'days': list(occupied_days),
        }, status=status.HTTP_200_OK)
