# permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Group, Activity


class IsGroupAdminOrMemberReadOnly(BasePermission):
    """
    - For Groups:
        - Read: Public groups or user is a member
        - Write: Only admin or owner
    - For Activities:
        - Read: Based on group visibility or membership
        - Write: Only admin or owner of the group
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if isinstance(obj, Group):
            group = obj
        elif isinstance(obj, Activity):
            group = obj.group
        else:
            return False

        if request.method in SAFE_METHODS:
            return group.visibility == Group.Visibility.PUBLIC or group.is_member(user)

        if view.action in ['exit', 'enter', 'create_request']:
            return True

        return group.is_admin(user) or group.is_owner(user)

class IsGroupAdminOrSelfManage(BasePermission):
    """
    Permissions for GroupMember:
    - CREATE (POST): any authenticated user
    - READ (GET, LIST): everyone (safe methods allowed)
    - EDIT/DELETE:
        - group admins can edit/delete anyone in the group
        - users can DELETE their own membership (self-remove)
    """

    def has_permission(self, request, view):
        # Anyone authenticated can CREATE
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        # Allow GET, LIST, and others to pass to object-level permission
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            # Allow safe methods for everyone
            return True

        # Group admins can edit/delete any membership in their group
        if obj.group.is_admin(user):
            return True

        # Users can DELETE their own membership (self-remove)
        if request.method == 'DELETE' and obj.user == user:
            return True

        if view.action == 'handle_privilege' and (obj.group.is_admin(user) or obj.group.is_owner(user)):
            return True

        return False


class IsSelfReadUpdateOnly(BasePermission):
    """
    Allow only the user to GET (retrieve) and UPDATE (PUT/PATCH) their own user instance.
    Disable create (POST) and delete (DELETE) entirely.
    """

    def has_permission(self, request, view):
        # Disable POST and DELETE globally
        if request.method in ['POST', 'DELETE']:
            return False
        # Allow other methods to pass to object-level permission
        return True

    def has_object_permission(self, request, view, obj):
        # Allow safe methods (GET) and update methods only if user matches the object
        if request.method in SAFE_METHODS or request.method in ['PUT', 'PATCH']:
            return obj == request.user
        # Otherwise deny
        return False
