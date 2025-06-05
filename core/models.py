from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from shared.models import UUIDChronoModel
from upload.models import ImageUpload
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **fields):
        user = self.create_user(
            email,
            **fields,
            password=password
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(UUIDChronoModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    avatar = models.ForeignKey(ImageUpload, on_delete=models.CASCADE, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self) -> str:
        return self.email


class Group(UUIDChronoModel):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', _('Public')
        PRIVATE = 'private', _('Private')

    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255)
    cover = models.ForeignKey(ImageUpload, on_delete=models.DO_NOTHING, null=True, blank=True)
    visibility = models.CharField(
        max_length=15,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    def is_member(self, user):
        return self.members.select_related('user').filter(user=user, is_pending_approval=False).exists()

    def is_owner(self, user):
        return self.members.select_related('user').filter(user=user, is_owner=True).exists()

    def is_admin(self, user):
        return self.members.select_related('user').filter(user=user, is_admin=True).exists()

    def members_list(self):
        return self.members.select_related('user').filter(is_pending_approval=False, is_owner=False)

    def owner(self):
        return self.members.select_related('user').filter(is_owner=True).first()

    def __str__(self):
        return self.name


class GroupMember(UUIDChronoModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_pending_approval = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.group.name} - {self.user.name}'


class Activity(UUIDChronoModel):
    class Modality(models.TextChoices):
        PUBLIC = 'online', _('Online')
        PRIVATE = 'in_person', _('In Person')

    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, null=True, blank=True)
    datetime = models.DateTimeField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='activities')
    address = models.CharField(null=True, blank=True, max_length=255)
    link = models.URLField(null=True, blank=True)

    modality = models.CharField(
        choices=Modality.choices,
        default=Modality.PUBLIC,
        max_length=15
    )

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_activities',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
