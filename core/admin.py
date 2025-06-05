from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Group, GroupMember, Activity


class ActivityInline(admin.TabularInline):  # or admin.StackedInline
    model = Activity
    extra = 0
    fields = ('name', 'datetime', 'modality')
    readonly_fields = ('name', 'datetime', 'modality')
    show_change_link = True  # Allows clicking through to edit activity

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    inlines = [ActivityInline]


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'user', 'is_owner', 'is_admin')
    list_filter = ('is_owner', 'is_admin', 'group')
    search_fields = ('group__name', 'user__name')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'datetime')
    list_filter = ('group', 'datetime')
    search_fields = ('name', 'description', 'group__name')
    ordering = ('-datetime',)

